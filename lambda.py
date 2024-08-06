import json
import requests
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Reservation:

    def __init__(self) -> None:
        self.API_KEY='no_limits'
        self.COURSE_ID=19765
        
        self.userReservations = []
        self.loginJwt = None
        self.current_tiles = []
        self.selected_tile = {}
        self.current_reservation_id = None
        self.cookie = None

        self.booking_email = None
        self.booking_password = None
        self.booking_class = None
        self.user_date_str= None
        self.user_start_time_str= None
        self.user_end_time_str= None
        self.players_input= None
        self.receiver_email= None
        self.name = None
        self.email_cc_text = []
        self.courses_selected = []
        self.course_names = []
        self.course_values = []

    def get_website_cookie(self):
        try:
            headers = {
                'Content-Type': 'text/html; charset=UTF-8'
            }
            response = requests.get("https://foreupsoftware.com/index.php/booking/19765", headers=headers)

            if response.status_code == 200:
                header_cookie = response.headers.get("set-cookie")
                self.cookie = header_cookie
                print(header_cookie)
            else:
                raise Exception("Error")
        except Exception as e:
            raise Exception(e)

    def loginHandler(self):
        try:
            payload = {
                'username': self.booking_email,
                'password': self.booking_password,
                'booking_class_id': '',
                'api_key': self.API_KEY,
                'course_id': self.COURSE_ID
            }

            headers = {
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                "Cookie": self.cookie
            }
            response = requests.post("https://foreupsoftware.com/index.php/api/booking/users/login", data=payload, headers=headers)

            if response.status_code == 200:
                
                res_data = response.json()

                if res_data['status_flag'] == '0' or res_data['status_flag'] == '2':
                    self.loginJwt = res_data['jwt']
                    self.userReservations = res_data['reservations']
                    log.info('Login Success')
                else:
                    raise Exception("Login Error")
            elif response.status_code == 401:
                raise Exception("Login Error")
            else:
                raise Exception("Error")
        except Exception as e:
            raise Exception(e)
    
    def cancel_reservations(self):
        try:

            if len(self.userReservations) == 0:
                return

            headers = {
                'Content-Type': 'application/json, text/javascript, */*; q=0.01',
                'X-Authorization': f'Bearer {self.loginJwt}',
                'Api-Key': self.API_KEY,
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
                "Cookie": self.cookie
            }

            res_TTID = self.userReservations[0]['TTID']

            if res_TTID == None:
                raise Exception("Error")

            response = requests.delete(f"https://foreupsoftware.com/index.php/api/booking/users/reservations/{res_TTID}", headers=headers)

            if response.status_code == 200:
                log.info("Previous Reservations Cancelled")
                return
            else:
                raise Exception("Error")
            
        except Exception as e:
            raise Exception(e)

    def part_of_day(self):
        time1 = datetime.strptime(self.user_start_time_str, '%H:%M').time()
        time2 = datetime.strptime(self.user_end_time_str, '%H:%M').time()

        if time1 >= datetime.strptime('06:00', '%H:%M').time() and time2 < datetime.strptime('12:00', '%H:%M').time():
            return 'morning'
        elif time1 >= datetime.strptime('12:00', '%H:%M').time() and time2 < datetime.strptime('17:00', '%H:%M').time():
            return 'midday'
        elif time1 >= datetime.strptime('17:00', '%H:%M').time() and time2 < datetime.strptime('21:00', '%H:%M').time():
            return 'evening'
        else:
            return 'all'
        
    def checkTiles(self, id):
        try:
            query_string = {
                "time": self.part_of_day(),
                "date": self.user_date_str,
                "holes": "all",
                "players": self.players_input,
                "booking_class": self.booking_class,
                "schedule_id": f"{id}",
                "schedule_ids[]": [
                    "2517",
                    "2431",
                    "2433",
                    "2539",
                    "2538",
                    "2434",
                    "2432",
                    "2435"
                ],
                "specials_only": "0",
                "api_key": self.API_KEY
            }

            headers = {
                'Content-Type': 'application/json, text/javascript, */*; q=0.01',
                'X-Authorization': f'Bearer {self.loginJwt}',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
                "Cookie": self.cookie
            }
            response = requests.get("https://foreupsoftware.com/index.php/api/booking/times", params=query_string, headers=headers)

            if response.status_code == 200:
                res_data = response.json()

                if len(res_data) > 0:
                    self.current_tiles = res_data
                    return True
                else:
                    return False
            else:
                return False
        except Exception as e:
            return False

    def pending_request(self,payload):
        try:
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'X-Authorization': f'Bearer {self.loginJwt}',
                'Api-Key': self.API_KEY,
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
                "Cookie": self.cookie
            }
            response = requests.post("https://foreupsoftware.com/index.php/api/booking/pending_reservation", data=payload, headers=headers)

            if response.status_code == 200:
                res_data = response.json()
                self.current_reservation_id = res_data['reservation_id'] 
                return True
            else:
                return False
            
        except Exception as e:
            return False

    def reserver_booking(self):
        try:
            if len(self.current_tiles) == 0:
                raise Exception("No tiles")
            
            for tile in self.current_tiles:
                time,holes,players,schedule_id,teesheet_side_id,course_id,booking_class_id,foreup_discount,foreup_trade_discount_rate,trade_min_players,cart_fee,cart_fee_tax,green_fee,green_fee_tax = (tile.get('time'),
                                 tile.get('holes'),
                                 tile.get('minimum_players'),
                                 tile.get('schedule_id'),
                                 tile.get('teesheet_side_id'),
                                 tile.get('course_id'),
                                 tile.get('booking_class_id'),
                                 tile.get('foreup_discount'),
                                 tile.get('foreup_trade_discount_rate'),
                                 tile.get('trade_min_players'),
                                 tile.get('cart_fee'),
                                 tile.get('cart_fee_tax'),
                                 tile.get('green_fee'),
                                 tile.get('green_fee_tax'),)
                
                payload = {
                    'time': time,
                    'holes': holes,
                    'players': players,
                    'carts': False,
                    'booking_class': booking_class_id,
                    'duration': 1,
                    'foreup_discount': foreup_discount,
                    'foreup_trade_discount_rate': foreup_trade_discount_rate,
                    'trade_min_players': trade_min_players,
                    'cart_fee': cart_fee,
                    'cart_fee_tax': cart_fee_tax,
                    'green_fee': green_fee,
                    'green_fee_tax': green_fee_tax,
                    'teesheet_side_id': teesheet_side_id,
                    'schedule_id': schedule_id,
                    'course_id': course_id,
                }

                isDone = self.pending_request(payload=payload)
                if isDone == True:
                    self.selected_tile = tile
                    break
                else:
                    continue

            if self.current_reservation_id == None:
                raise Exception("No reservation ID")

        except Exception as e:
            raise Exception(e)

    def send_email(self, reservation):
        try:
            bot_email = "my.golf.reservations@gmail.com"
            bot_app_password = "fngxdahigivgtztq"

            reservation_info = f"Hi {self.name},<br/>Congratulations, I have booked a reservation for you! Below are the details for your reservation:<br/><br/>Course : {reservation['teesheet_title']}<br/>Date & Time : {reservation['time']}<br/>Players : {reservation['player_count']}<br/><br/>Enjoy! <br/><b>RezShark</b>"

            body = MIMEText(reservation_info, 'html')

            email_message = MIMEMultipart()
            email_message['From'] = bot_email
            email_message['To'] = self.receiver_email
            email_message['Subject'] = "Tee Time Reservation"

            email_message.attach(body)

            if self.email_cc_text:
                email_message['CC'] = ', '.join(self.email_cc_text)
            email_text = email_message.as_string()

            with smtplib.SMTP("smtp.gmail.com", 587) as smtpserver:
                smtpserver.ehlo()
                smtpserver.starttls()
                smtpserver.ehlo()
                smtpserver.login(bot_email, bot_app_password)
                recipients = [self.receiver_email] + self.email_cc_text
                smtpserver.sendmail(bot_email, recipients, email_text)

            log.info("Mail Send Successfully")
        except Exception as e:
            log.info("Error sending email")

    def refresh_pending_reservation(self):
        try:
            headers = {
                'X-Authorization': f'Bearer {self.loginJwt}',
                'Api-Key': self.API_KEY,
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
                "Cookie": self.cookie
            }
            response = requests.post(f"https://foreupsoftware.com/index.php/api/booking/refresh_pending_reservation/{self.current_reservation_id}", headers=headers)

            if response.status_code == 200:
                return
            else:
                raise Exception("Failed to refresh reservation")

        except Exception as e:
            raise Exception(e)

    def confirm_booking(self):
        try:
            if self.current_reservation_id == None:
                raise Exception("No reservation ID")
            
            self.refresh_pending_reservation()

            payload = {
                **self.selected_tile,
                "airQuotesCart": [
                    {
                        "description": "Green Fee",
                        "price": self.selected_tile['green_fee'],
                        "quantity": 1,
                        "subtotal": self.selected_tile['green_fee'],
                        "type": "item"
                    }
                ],
                "allow_mobile_checkin": 0,
                "available_duration": None,
                "availableHoles": "18",
                "blockReservationDueToExistingReservation": False,
                "captchaid": "",
                "carts": False,
                "customer_message": "",
                "details": "",
                "discount": 0,
                "discount_percent": 0,
                "duration": 1,
                "estimatedTax": 0,
                "foreup_trade_discount_information":[],
                "increment_amount": None,
                "notes": [],
                "paid_player_count": 0,
                "pay_carts": False,
                "pay_players": "1",
                "pay_subtotal": self.selected_tile['green_fee'],
                "pay_total": self.selected_tile['green_fee'],
                "pending_reservation_id": self.current_reservation_id,
                "player_list": False,
                "players": f"{self.players_input}",
                "preTaxSubtotal": self.selected_tile['green_fee'],
                "promo_code": "",
                "promo_discount": 0,
                "purchased": False,
                "subtotal": self.selected_tile['green_fee'],
                "total": self.selected_tile['green_fee']
            }

            headers = {
                'Content-Type': 'application/json',
                'X-Authorization': f'Bearer {self.loginJwt}',
                'Api-Key': self.API_KEY,
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
                "Cookie": self.cookie
            }
            response = requests.post("https://foreupsoftware.com/index.php/api/booking/users/reservations", json=payload, headers=headers)
            res_data = response.json()

            if response.status_code == 200:

                log.info("Booking completed")
                self.send_email(res_data)
                return True
            else:
                raise Exception("Reservation Failed")

        except Exception as e:
            raise Exception(e)

# def start_script():
#     try:
#         res = Reservation()
#         res.booking_email = "w9jhul@givememail.club"
#         res.booking_password = "admin123"
#         res.user_date_str = "08-04-2024"
#         res.user_start_time_str = "06:00"
#         res.user_end_time_str = "23:00"
#         res.players_input = 1
#         res.receiver_email = "w9jhul@givememail.club"
#         res.name = "bot"
#         res.email_cc_text = ["964ruc@givememail.club", "964ruc@givememail.club"]
#         res.courses_selected = [2431, 2433, 2432, 2435]
#         res.course_names = ["Black course","Blue course","Red course", "Yellow course"]
#         res.course_values = [2431, 2433, 2432, 2435]

#         res.get_website_cookie()
#         res.loginHandler()
        
#         for course in res.courses_selected:
#             haveTitles =  res.checkTiles(course)
#             if haveTitles == True:
#                 break
        
#         if len(res.current_tiles) == 0:
#             raise Exception("No tiles")

#         res.cancel_reservations()
#         res.reserver_booking()
#         res.confirm_booking()

#     except Exception as e:
#         log.info("RESTART: Error")
        
#         return {
#             'statusCode': 400,
#             'body': json.dumps('Script Failed, Some Issue!')
#         }

# start_script()

def lambda_handler(event, context):
    try:
        res = Reservation()
        res.booking_email = event.get('booking_email')
        res.booking_password = event.get('booking_password')
        res.user_date_str = event.get('user_date_str')
        res.user_start_time_str = event.get('user_start_time_str')
        res.user_end_time_str = event.get('user_end_time_str')
        res.players_input = event.get('players_input')
        res.receiver_email = event.get('receiver_email')
        res.name = event.get('name')
        res.booking_class = int(event.get('booking_class'))
        res.email_cc_text = event.get('email_cc_text')
        res.course_names=event.get('course_names')
        course_vals=event.get('course_values')
        res.course_values = list(map(str, course_vals))
        res.courses_selected = list(map(str, course_vals))

        res.get_website_cookie()
        res.loginHandler()
        
        for course in res.courses_selected:
            haveTitles =  res.checkTiles(course)
            if haveTitles == True:
                break
        
        if len(res.current_tiles) == 0:
            raise Exception("No tiles")

        res.cancel_reservations()
        res.reserver_booking()
        res.confirm_booking()

        return {
            'statusCode': 200,
            'body': json.dumps('Hello, World!')
        }
    except Exception as e:
        log.info("RESTART: Error")
        return {
            'statusCode': 400,
            'body': json.dumps('Script Failed, Some Issue!')
        }