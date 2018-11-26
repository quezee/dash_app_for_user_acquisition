import gspread
from oauth2client.service_account import ServiceAccountCredentials

class GoogleSheet:
    
    def __init__(self):
        self.scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        self.credentials = ServiceAccountCredentials.from_json_keyfile_name('keys/google_key.json', self.scope)
        
    def open_url(self, url):
        gc = gspread.authorize(self.credentials)
        sheet = gc.open_by_url(url)
        return sheet