"""
This file is base for dataset sweep intiators, implements sweep progress persistency and other common logic
"""
import requests
from abc import ABC, abstractmethod
from typing import List, Tuple

from src.mongo.interface import Sessions


class BaseInitiator(ABC):

    @property
    @abstractmethod
    def BASE_URLS(self): ...

    @abstractmethod
    def parse_file_page(self, response: requests.Response) -> List[str]:
        ...

    @abstractmethod
    def create_celery_tasks(self, urls: List[str]) -> List[str]:
        """Returns list of assigned urls"""
        ...

    @property
    def task_collection_name(self):
        return f"tasks-{self.tolerance:.4f}"

    @property
    def dataheap_collection_name(self):
        return f"dataheap-{self.tolerance:.4f}"

    def __init__(self, tolerance: int):
        """
        tolerance: int - radius around the lunar pits to be considered for data collection
        """
        self.tolerance = tolerance
        self.db_session = Sessions.get_db_session(db_name=self.DATASET_NAME)
        self.local_task_stack = []

    def create_folder_task(self, url: str):
        self.db_session[self.task_collection_name].insert_one(
            {"url": url, "task_finished": False, "is_folder": True, "assigned": False}
        )
        self.db_session.commit()

    def finish_folder_task(self, url: str):
        self.db_session[self.task_collection_name].update_one({"url": url}, {"$set": {"task_finished": True}})
        self.db_session.commit()

    def create_file_tasks(self, urls: List[str]):
        """
        Create tasks for the files in bulk
        """
        self.db_session[self.task_collection_name].insert_many(
            [{"url": url, "task_finished": False, "is_folder": False, "assigned": False} for url in urls]
        )
        self.db_session.commit()
        assigned_urls = self.create_celery_tasks(urls)
        self.db_session[self.task_collection_name].update_many(
            {"url": {"$in": assigned_urls}}, {"$set": {"assigned": True}}
        )
        self.db_session.commit()

    def process_url(self, url: str) -> Tuple[List[str], List[str]]:
        response = requests.get(url)
        response.raise_for_status()
        return self.parse_file_page(response)

    def execute_tasks(self):
        while self.local_task_stack:
            url = self.local_task_stack.pop()
            folders_url, files_url = self.process_url(url)
            self.finish_folder_task(url)

            self.local_task_stack.extend(folders_url)
            self.create_file_tasks(files_url)

    def sweep(self):
        self.local_task_stack = self.BASE_URLS
        for url in self.BASE_URLS:
            self.create_folder_task(url)
        self.execute_tasks()


    def continue_sweep(self):
        """
        Continue the sweep by resuming from the unfinished folder tasks in MongoDB.
        """
        unfinished_folders = self.db_session[self.task_collection_name].find(
            {"is_folder": True, "task_finished": False}
        )
        assigned_unifinished_tasks = self.db_session[self.task_collection_name].find(
            {"is_folder": False, "task_finished": False, "assigned": True}
        )
        self.create_file_tasks([task["url"] for task in assigned_unifinished_tasks])
        self.local_task_stack = [folder["url"] for folder in unfinished_folders]
        self.execute_tasks()
