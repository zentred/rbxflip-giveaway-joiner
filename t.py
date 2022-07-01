import cloudscraper, ctypes, time, json, os, requests
from threading import Thread
from colorama import init, Fore
init()
scraper = cloudscraper.create_scraper(browser={'browser': 'firefox','platform': 'windows','mobile': False})

currentSecond = 0
foundGiveaways = 0
joinedGiveaways = 0
loaded = 0
failed = 0
already_gw = []
my_users = []

os.system('cls')

config = json.load(open('config.json','r'))
bearer_tokens = config['bearer_tokens']
webhook = config['webhook']
discord_id = config['discord_id']

def title():
    while True:
        ctypes.windll.kernel32.SetConsoleTitleW(f'Accounts Loaded: {loaded}/{failed} | Found Giveaways: {foundGiveaways} | Joined Giveaways: {joinedGiveaways} | Rechecking Giveaways In: {currentSecond}/15')
        time.sleep(0.1)

def checkGiveaway():
    global currentSecond, foundGiveaways, already_gw
    while True:
        try:
            giveaway = scraper.get("https://legacy.rbxflip-apis.com/giveaways").json()
            for gw in giveaway['data']['giveaways']:

                holder = gw['holder']['name']
                itemName = gw['item']['name']
                itemValue = gw['item']['value']

                if gw['status'] == 'Completed':
                    if gw['winner']['name'] in my_users:

                        data = {
                            'content': '<@{discord_id}>',
                            'embeds':[{
                                'color': int('129b19',16),
                                'fields': [
                                    {'name': f"You won the giveaway on {gw['winner']['name']}" ,'value': f'{itemName} (**{itemValue}**)','inline':False},
                                ]
                            }]
                        }
                        requests.post(webhook, json=data)
                else:
                    if gw['_id'] not in already_gw:
                        already_gw.append(gw['_id'])
                        foundGiveaways += 1

                        print(f'[{Fore.LIGHTCYAN_EX}+{Fore.WHITE}] Giveaway found > {Fore.LIGHTCYAN_EX} {itemName} (Value: {itemValue})')

                        data = {
                            'embeds':[{
                                'color': int('2e88f5',16),
                                'fields': [
                                    {'name': f'{holder} is giving away a limited!' ,'value': f'{itemName} (**{itemValue}**)','inline':False},
                                ]
                            }]
                        }
                        requests.post(webhook, json=data)

            while True:
                time.sleep(1)
                currentSecond += 1
                if currentSecond == 15:
                    currentSecond = 0
                    break
        except:
            time.sleep(15)
            pass

class User:

    def __init__(self, token):
        self.bearer = token
        self.headers = {'authorization': f'Bearer {self.bearer}'}
        self.current_gw = []
        self.passed = []
        self.username = ''
        self.validate = False
        self.checkUser()
        if self.validate == True:
            Thread(target=self.checkGlobalGw).start()
            Thread(target=self.enterGiveaway).start()

    def checkUser(self):
        global my_users, loaded, failed
        info = scraper.get('https://legacy.rbxflip-apis.com/auth/user', headers=self.headers).json()
        if 'ok' in info:
            user = info['data']['user']['name']
            self.username = user
            if info['data']['user']['gamesPlayed'] == 0:
                print(f'[{Fore.RED}-{Fore.WHITE}] User has not played any games > {Fore.RED}{user}{Fore.WHITE}')
                failed += 1
            else:
                print(f'[{Fore.LIGHTCYAN_EX}+{Fore.WHITE}] {Fore.LIGHTCYAN_EX}{user} {Fore.WHITE} was added to account list')
                my_users.append(user)
                loaded += 1
                self.validate = True
        else:
            failed += 1
            print(f'[{Fore.RED}-{Fore.WHITE}] Bearer token was invalid > {Fore.RED}{self.bearer[-10:]} {Fore.WHITE}(last 10 characters of token)')

    def checkGlobalGw(self):
        global already_gw
        while True:
            for x in already_gw:
                if x not in self.current_gw:
                    self.current_gw.append(x)
            time.sleep(1)

    def enterGiveaway(self):
        global joinedGiveaways
        while True:
            for gw in self.current_gw:
                if gw not in self.passed:
                    self.passed.append(gw)
                    join = scraper.put(f'https://legacy.rbxflip-apis.com/giveaways/{gw}', headers=self.headers).json()
                    if 'ok' in join and join['ok']:
                        print(f'[{Fore.GREEN}+{Fore.WHITE}] {self.username} joined the giveaway')
                        data = {
                            'embeds':[{
                                'color': int('e07800',16),
                                'fields': [
                                    {'name': f'{self.username} joined the giveaway' ,'value': f'\u200b','inline':False},
                                ]
                            }]
                        }
                        requests.post(webhook, json=data)
                        joinedGiveaways += 1
                    elif '24' in str(join):
                        data = {
                            'embeds':[{
                                'color': int('e07800',16),
                                'fields': [
                                    {'name': f'{self.username} is unable to join the giveaway' ,'value': f'No games played in the past 24 hours','inline':False},
                                ]
                            }]
                        }
                        requests.post(webhook, json=data)
                    else:
                        data = {
                            'embeds':[{
                                'color': int('e07800',16),
                                'fields': [
                                    {'name': f'Dont know' ,'value': f'Couldnt be bothered to check the other responses so send this to Turn\n{str(join)}','inline':False},
                                ]
                            }]
                        }
                        requests.post(webhook, json=data)
            time.sleep(1)


for bearer in bearer_tokens:
    c = User(bearer)

Thread(target=checkGiveaway).start()
Thread(target=title).start()

print(f'\nBearer tokens were checked > {Fore.GREEN}{loaded}{Fore.WHITE} accounts loaded / {Fore.RED}{failed} {Fore.WHITE}accounts not loaded')
