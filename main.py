import json
import time
import webbrowser
import requests
from fake_useragent import UserAgent
from hashlib import md5
from bs4 import BeautifulSoup
from config import API_TOKEN, CHAT_ID, LOGIN, PASSWORD, UID_FILE


class Message:
    url_login = 'https://backoffice.algoritmika.org/auth/login'
    url_main = 'https://backoffice.algoritmika.org'

    def auth(self):
        client = requests.session()
        request = client.get(self.url_login)
        cookies = request.cookies.get_dict()
        soup = BeautifulSoup(request.text, 'html.parser')

        csrf = soup.find('input', dict(name='_csrf'))['value']

        data = {
            'LoginForm[username]': LOGIN,
            'LoginForm[password]': PASSWORD,
            'LoginForm[rememberMe]': 1,
            '_csrf': csrf
        }

        headers = {
            'User-Agent': UserAgent().random,
            'Referer': self.url_main,
        }

        request = client.post(self.url_login, cookies=cookies, data=data, headers=headers)

        return request.status_code, client

    def new_projects(self):
        url = 'https://backoffice.algoritmika.org/api/v1/teacherComment/projects?from=0&limit=30'
        if self.auth()[0] == 200:
            client = self.auth()[1]
            request = client.get(url)
            get_projects = json.loads(request.text)
            projects = get_projects['data']['projects']
            if len(projects) > 0:
                for m in projects:
                    content_hash = md5(str(m['uid'] + m['content']).encode()).hexdigest()
                    if not self.get_uid(content_hash) and m['new'] and m['senderScope'] == 'student':
                        msg = f"[Алгоритмика] {m['name']} \n {m['content']}"
                        self.send_message(msg)
                        self.add_uid(content_hash)
                        # self.browse_url(f"{self.url_main}{m['link']}")
        else:
            print(self.auth()[0])

    def send_message(self, msg):
        url = f'https://api.telegram.org/bot{API_TOKEN}/sendMessage?chat_id={CHAT_ID}&text={msg}'
        response = requests.get(url)
        return response

    def read_project(self, uid):
        url = 'https://backoffice.algoritmika.org/platform/api/v1/teacherComment/read'
        response = requests.get(url)
        return response

    def browse_url(self, url):
        webbrowser.register('chrome', None, webbrowser.BackgroundBrowser(
            "C://Program Files (x86)//Google//Chrome//Application//chrome.exe"))
        webbrowser.get('chrome').open(url)

    def get_uid(self, uid):
        with open(UID_FILE, 'r') as uid_file:
            uid_list = uid_file.read().split(",")
            return uid in uid_list

    def add_uid(self, uid):
        with open(UID_FILE, 'a') as uid_file:
            uid_file.write(f"{uid},")


if __name__ == '__main__':
    obj = Message()

    while True:
        try:
            obj.new_projects()
        except requests.exceptions.HTTPError as err:
            print("HTTP Error:", err)
        except requests.exceptions.ConnectionError as err:
            print("Error Connecting:", err)
        except requests.exceptions.Timeout as err:
            print("Timeout Error:", err)
        except requests.exceptions.RequestException as err:
            print("Error!", err)
        time.sleep(5)
