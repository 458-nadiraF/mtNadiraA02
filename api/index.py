from http.server import BaseHTTPRequestHandler
import json
import requests
import traceback
import os
import time
class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type','text/plain')
        self.end_headers()
        self.wfile.write('Hello, world!'.encode('utf-8'))
        return
    def get_account_balance(self,token, account):
        headers = {
            'Accept': 'application/json',
            'auth-token': token 
        }
        
        try:
            get_balance_url=f"https://mt-client-api-v1.london.agiliumtrade.ai/users/current/accounts/{account}/account-information"
            response = requests.get(get_balance_url, headers=headers)
            
            # Check if request was successful
            if response.status_code == 200:
                data = response.json()
                return data.get('balance')  
            else:
                print(f"Error: API request for get balance failed with status code {response.status_code}")
                print(response) 
                return None
                
        except Exception as e:
            print(f"Error fetching balance: {str(e)}")
            return None
    def do_POST(self):
        # terima alert dr tv
      
        try:
            start_time = time.time()
            content_length = int(self.headers.get('Content-Length', 0))  # Default to 0 if not present
            if content_length > 0:
                post_data = self.rfile.read(content_length).decode('utf-8')  # Decode bytes to string
            else:
                post_data = ""  # No data sent
            
            if not post_data.strip():  # Check if the body is empty or whitespace
                raise ValueError("Empty request body")
            
            # Parse JSON
            received_json = json.loads(post_data)
            print(received_json)
            #received_json = json.loads(post_data.decode('utf-8'))
            message=received_json.get('plain')
            messageSplit=message.split()
            closePrice1=messageSplit[1]
            closePrice=closePrice1.split('\n')[0]
            action=messageSplit[0] 
            # accountName=received_json.get('account')
            accountStr=f'ACCOUNT_ID'
            tokenStr=f'METAAPI_TOKEN'
            account=os.getenv(accountStr)
            token=os.getenv(tokenStr)
            # a=0
            # if accountName=="masnur":
            #     if symbol[-1]!='m' :
            #         symbol=f'{symbol}m'
            #     a=1
            # else:
            #     if symbol[-1]=='m' :
            #         symbol=symbol[0:-1]
            balance=self.get_account_balance(token, account)
            # Define the API endpoint where you want to forward the request
            forward_url = f"https://mt-client-api-v1.london.agiliumtrade.ai/users/current/accounts/{account}/trade"  # Replace with your actual API endpoint
            balance2= float(balance) 
            actType=""
            if action=="BUY" or action=="SELL":
                if(action=="BUY"):
                  actType="ORDER_TYPE_BUY"
                    
                if(action=="SELL") :
                    actType="ORDER_TYPE_SELL"
                lot=0.8*balance2/(0.16*float(closePrice))
                sll=float(closePrice)*(0.0016)*100
                buy_json={
                    "symbol": "XAUUSDm",
                    "actionType": actType,
                    "volume": round(float(lot), 2),
                    "stopLoss": sll,
                    "stopLossUnits":"RELATIVE_PIPS"
                }
            if(action=="EXIT"):
                buy_json={
                    "symbol": "XAUUSDm",
                    "actionType": "POSITIONS_CLOSE_SYMBOL"                }
            
            headers = {
                'Accept': 'application/json',
                'auth-token':token,
                'Content-Type':'application/json'
                # Add any other required headers here
            }
            
            response = requests.post(
                forward_url,
                json=buy_json,
                headers=headers
            )
            
            execution_duration = (time.time() - start_time) * 1000
            # Send response back to the original client
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            # You can customize the response based on the forwarded request's response
            response_data = {
                "message": "POST received and forwarded",
                "forward_status": response.status_code,
                "received_json":received_json,
                "buy_json": buy_json, 
                "forward_response": response.json()  # Include this if you want to return the forwarded API's response
            }
            self.wfile.write(json.dumps(response_data).encode())
           
            log_message = (
                f" MTNadira A02. Execution Duration: {execution_duration}ms\n"
                f"Response Content: {response_data}\n"
                "-------------------------------------------\n"
            )
            headers2 = {
                'Accept': 'application/json',
                'Content-Type':'application/json'
                # Add any other required headers here
            }
            response = requests.post(
                    os.getenv('SPREADSHEET'),
                    json=log_message,
                    headers=headers2
                )
            print(response_data)
            if response.status_code == 200:
                return None
            else:
                print(f"Error: API request for placing order failed with status code {response.status_code}")
                return None
            tele_url=os.getenv('TELEGRAM_API')
            timestamp=timestamp = time.strftime("%m/%d/%Y %H:%M:%S", time.localtime())
            # Define the API endpoint where you want to forward the request
            textContent=f"Alert Screener A02:Any alert() function call \n{log_message}"
            params={
               "chat_id": f"{os.getenv('CHAT_ID')}",
               "text": textContent
            }
            
            response = requests.post(
                tele_url,
                params=params
            )
        except Exception as e:
            # Handle any errors
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            error_response = {
                "error": str(e),
                "message": "Error processing request"
            }
            traceback.print_exc()
            self.wfile.write(json.dumps(error_response).encode())
