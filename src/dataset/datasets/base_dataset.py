import asyncio
import os
import logging
import requests
from requests import Response
from typing import List, Dict
from abc import ABC, abstractmethod
from urllib.parse import urljoin

import httpx
import aiofiles
from tqdm.asyncio import tqdm
from rich.tree import Tree
from rich import print as rprint


class AbstractDatasetLRO(ABC):

    def __init__(self, dataset_root_url: str, remote_root_path: str, local_root_path: str):
        self.dataset_root_url = dataset_root_url
        self.remote_root_path = remote_root_path
        self.local_root_path = local_root_path

    @abstractmethod
    def folder_file_interest(self, filename: str) -> bool:
        pass

    @abstractmethod
    def parse_file_page(self, response: Response) -> Dict[str, List[tuple[str, str]]]:
        """tuple(url, filename/foldername(relative))"""
        pass

    async def print_local_ds_state(self):
        self.print_tree(
            self.diff_files(self.list_local_files(), await self.list_remote_files()),
            "Current state of the local dataset",
        )

    def handle_file_page(self, url: str) -> Dict[str, List[tuple[str, str]]]:
        try:
            response = requests.get(url)
            response.raise_for_status()
            return self.parse_file_page(response)
        except Exception as e:
            logging.warning(f"Failed to fetch {url}\n{e}")
            return {"files": [], "folders": []}

    async def download_file(
        self, url: str, filename: str, local_path: str, pbar: tqdm | None, semaphore: asyncio.Semaphore
    ) -> None:
        """Download a file asynchronously."""
        try:
            async with semaphore, httpx.AsyncClient() as client, client.stream("GET", url, timeout=120) as response:
                response.raise_for_status()
                total_size = int(response.headers.get("content-length", 0))
                file_path = os.path.join(local_path, filename)
                os.makedirs("/".join(file_path.split("/")[:-1]), exist_ok=True)
                async with aiofiles.open(file_path, "wb") as f:
                    # Initialize a local progress bar if no pbar is passed
                    local_pbar = pbar or tqdm(total=total_size, unit="B", unit_scale=True, desc=filename)
                    async for chunk in response.aiter_bytes():
                        if chunk:
                            await f.write(chunk)
                            if local_pbar:
                                local_pbar.update(len(chunk))
                    if not pbar:  # Close local progress bar if it was created here
                        await local_pbar.close()
        except Exception as e:
            logging.warning(f"Failed to download {url} to {os.path.join(local_path, filename)}\n{e}")

    async def probe_file(self, url: str, semaphore: asyncio.Semaphore) -> int:
        """Return file size in bytes asynchronously, with optional TQDM progress bar. Download the file if download_file is True."""
        try:
            async with semaphore, httpx.AsyncClient() as client, client.stream("GET", url, timeout=60) as response:
                response.raise_for_status()
                total_size = int(response.headers.get("content-length", 0))
        except Exception as e:
            logging.warning(f"Failed to probe {url}\n{e}")
        return total_size

    def list_local_files(self) -> List[Dict]:
        """
        Walk the local dataset root and return a list of tuples with each file’s path
        and its size (in bytes), only including files for which folder_file_interest returns True.
        """
        results = {}

        for root, _, files in os.walk(self.local_root_path):
            for file in files:
                if self.folder_file_interest(file):
                    file_path = os.path.join(root, file)
                    results[file_path] = {"size": os.path.getsize(file_path)}
        return results

    async def list_remote_files(self, max_wokers: int = 32) -> List[Dict]:
        """
        Walk through remote dataset and return list of file in format of dict, with url
        and relative path of the file to the dataset.
        """
        urls_to_visit = [
            {
                "url": urljoin(self.dataset_root_url, self.remote_root_path),
                "remote-prefix": ".",
            }
        ]
        results = {}
        semaphore = asyncio.Semaphore(max_wokers)

        async def process_file(file, remote_prefix):
            """Asynchronously get the size of a file and store the result."""
            size = await self.probe_file(file[0], semaphore)

            results[os.path.join(remote_prefix, file[1]).replace('.', self.local_root_path, 1)] = {
                "size": size,
                "url": file[0],
            }

        while urls_to_visit:
            url = urls_to_visit.pop()
            parsed_paths = self.handle_file_page(url["url"])

            tasks = [
                process_file(file, url["remote-prefix"])
                for file in parsed_paths["files"]
                if self.folder_file_interest(file[1])
            ]

            await asyncio.gather(*tasks)

            for folder in parsed_paths["folders"]:
                if self.folder_file_interest(folder[1]):
                    urls_to_visit.append(
                        {
                            "url": folder[0],
                            "remote-prefix": os.path.join(url["remote-prefix"], folder[1]),
                        }
                    )
        return results

    @staticmethod
    def print_tree(files: Dict[str, Dict], title: str):
        """
        Print a tree structure of files and folders using rich.Tree with color indicators based on status.

        Args:
            files: A dictionary of files with their paths, sizes, and statuses.
            title: The title for the root of the tree.
        """
        tree = Tree(title)
        nodes = {"/": tree}  # Dictionary to track nodes and sub-nodes

        for file_path, file_info in files.items():
            parts = file_path.split("/")
            file_size = file_info.get("size", "Unknown")
            status = file_info.get("status", "missing")

            # Choose color based on file status
            color = {"downloaded": "green", "corrupted": "yellow", "not_downloaded": "red"}.get(status)

            # Traverse through folder hierarchy and add nodes
            current_path = "/"
            for part in parts[:-1]:  # Traverse folders only
                current_path = f"{current_path}/{part}" if current_path != "/" else part
                if current_path not in nodes:
                    nodes[current_path] = nodes[
                        "/" if current_path == part else "/".join(current_path.split("/")[:-1])
                    ].add(part)

            # Add the final file to the current folder node
            file_name = parts[-1]
            file_node = f"[{color}]{file_name} ({file_size} bytes) [{status}][/{color}]"
            nodes[current_path].add(file_node)

        rprint(tree)

    def diff_files(self, local_files: Dict, remote_files: Dict) -> Dict[str, Dict]:
        """
        Compare local and remote files and classify them with a status (downloaded, corrupted, or not_downloaded).

        Returns a unified dictionary with file paths, sizes, and statuses.
        """
        files_with_status = {}
        for file, remote_info in remote_files.items():
            if file in local_files:
                if local_files[file]["size"] == remote_info["size"]:
                    files_with_status[file] = {"size": remote_info["size"], "status": "downloaded"}
                else:
                    files_with_status[file] = {"size": remote_info["size"], "status": "corrupted"}
            else:
                files_with_status[file] = {"size": remote_info["size"], "status": "not_downloaded"}
            if remote_info.get("url"):
                files_with_status[file]["url"] = remote_info["url"]
        return files_with_status

    async def download_dataset(self, force_download: bool = False, max_workers: int = 3, file_tree: bool = False):
        """
        Download dataset files based on comparison between local and remote files.
        If force_download is False, only missing or corrupted files are downloaded.
        """
        local_files = {} if force_download else self.list_local_files()
        remote_files = await self.list_remote_files()

        files_with_status = self.diff_files(local_files, remote_files)
        if file_tree:
            self.print_tree(files_with_status, "Dataset Files")

        to_download = {
            file: info
            for file, info in files_with_status.items()
            if force_download or info["status"] in {"corrupted", "not_downloaded"}
        }

        to_download_size = sum(file_info["size"] for file_info in to_download.values())
        print(f"Downloading {len(to_download)} files ({to_download_size // (1024 * 1024)} MB)")

        semaphore = asyncio.Semaphore(max_workers)
        with tqdm(total=to_download_size, unit="B", unit_scale=True, desc="Downloading files") as pbar:
            tasks = [
                self.download_file(file_info["url"], filename, self.local_root_path, pbar, semaphore)
                for filename, file_info in to_download.items()
            ]
            await asyncio.gather(*tasks)
