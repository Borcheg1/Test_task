import os

import pygsheets
from dotenv import load_dotenv


class GoogleTible:
    def __init__(
            self,
            credence: str = "client_secret.json",
            sheet_url: str = "https://docs.google.com/spreadsheets/d/1TIy1zfCCm0m6mTXJBixx71lcqNRhOnWfhMCuQYbgV2g/edit#gid=0",
    ) -> None:
        self.credence = credence
        self.sheet_url = sheet_url

    def _get_sheet_by_url(
            self,
            sheet_client: pygsheets.client.Client
    ) -> pygsheets.Spreadsheet:
        sheets: pygsheets.Spreadsheet = sheet_client.open_by_url(
            self.sheet_url
        )
        return sheets.sheet1

    def _get_sheet_client(self):
        return pygsheets.authorize(service_file=self.credence)

    def add_row(self):
        sheet_client: pygsheets.client.Client = self._get_sheet_client()
        wks: pygsheets.Spreadsheet = self._get_sheet_by_url(sheet_client)
        wks.update_value('E1', 'test')


d = GoogleTible()
d.add_row()

