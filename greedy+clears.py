import requests
import math
import random
from time import sleep

s = requests.Session()
s.headers.update({'X-API-key': 'JXUUU6X3'}) # Dektop

MAX_LONG_EXPOSURE = 25000
MAX_SHORT_EXPOSURE = -25000
SPEEDBUMP = 0.5
ORDER_LIMIT = 1750

def get_tick():
    resp = s.get('http://localhost:9999/v1/case')
    if resp.ok:
        case = resp.json()
        return case['tick'], case['status']


def get_bid_ask(ticker):
    payload = {'ticker': ticker}
    resp = s.get ('http://localhost:9999/v1/securities/book', params = payload)
    if resp.ok:
        book = resp.json()
        bid_side_book = book['bids']
        ask_side_book = book['asks']
        
        bid_prices_book = [item["price"] for item in bid_side_book]
        ask_prices_book = [item['price'] for item in ask_side_book]
        
        best_bid_price = bid_prices_book[0]
        best_ask_price = ask_prices_book[0]
  
        return best_bid_price, best_ask_price


def get_time_sales(ticker):
    payload = {'ticker': ticker}
    resp = s.get('http://localhost:9999/v1/securities/tas', params = payload)
    if resp.ok:
        book = resp.json()
        time_sales_book = [item["quantity"] for item in book]
        return time_sales_book


def cancel_all():
    resp = s.post('http://localhost:9999/v1/commands/cancel', params = {'all': 1})


def get_position(ticker):
    resp = s.get ('http://localhost:9999/v1/securities')
    if resp.ok:
        book = resp.json()
        for t in book:
            if t['ticker'] == ticker:
                position = t['position']
        return position

def get_open_orders(ticker):
    payload = {'ticker': ticker}
    resp = s.get ('http://localhost:9999/v1/orders', params = payload)
    if resp.ok:
        orders = resp.json()
        buy_orders = [item for item in orders if item["action"] == "BUY"]
        sell_orders = [item for item in orders if item["action"] == "SELL"]
        return buy_orders, sell_orders

def get_order_status(order_id):
    resp = s.get ('http://localhost:9999/v1/orders' + '/' + str(order_id))
    if resp.ok:
        order = resp.json()
        return order['status']

def buy_limit(buy_price, ticker, order_size):
    print('')
    s.post('http://localhost:9999/v1/orders', params={'ticker': ticker, 'type': 'LIMIT', 'quantity': order_size,
                                                            'price': buy_price, 'action': 'BUY'})

def buy_sell(sell_price, ticker, order_size):
    print('')
    s.post('http://localhost:9999/v1/orders', params={'ticker': ticker, 'type': 'LIMIT', 'quantity': order_size,
                                                            'price': sell_price, 'action': 'SELL'})

def open_sells(session):
    resp = s.get('http://localhost:9999/v1/orders?status=OPEN')
    if resp.ok:
        open_sells_volume = 0
        ids = []
        prices = []
        order_volumes = []
        volume_filled = []
        open_orders = resp.json()
        for order in open_orders:
            if order['action'] == 'SELL':
                volume_filled.append(order['quantity_filled'])
                order_volumes.append(order['quantity'])
                open_sells_volume = open_sells_volume + order['quantity']
                prices.append(order['price'])
                ids.append(order['order_id'])
                
    return volume_filled,open_sells_volume,ids,prices,order_volumes

def re_order(session,number_of_orders,ids,volumes_filled,volumes,price,action):
    for i in range(number_of_orders):
        id_val = ids[i]
        volume = volumes[i]
        volume_filled = volumes_filled[i]
        if(volume_filled != 0 ):
            volume = MAX_VOLUME - volume_filled 
        
        #delete the repurchase
        deleted = session.delete("http://localhost:9999/v1/orders/{}".format(id_val))
        if deleted.ok:
            session.post('http://localhost:9999/v1/orders', params={'ticker': ticker, 'type': 'LIMIT', 'quantity': volume,
                                                                    'price': price, 'action': action})


def clear_all(ticker,position,best_bid_price,best_ask_price):
    if position> 0:
        while position > 2500:
            resp =  s.post('http://localhost:9999/v1/orders', params={'ticker': ticker, 'type': 'LIMIT', 'quantity': 2500,
                                                             'price': best_ask_price, 'action': 'SELL'})
            position -= 2500
        resp =  s.post('http://localhost:9999/v1/orders', params={'ticker': ticker, 'type': 'LIMIT', 'quantity': position,
                                                         'price': best_ask_price, 'action': 'SELL'})
    if position <0:
        while position < -2500:
            resp =  s.post('http://localhost:9999/v1/orders', params={'ticker': ticker, 'type': 'LIMIT', 'quantity': 2500,
                                                             'price': best_bid_price, 'action': 'BUY'})
            position += 2500
        resp =  s.post('http://localhost:9999/v1/orders', params={'ticker': ticker, 'type': 'LIMIT', 'quantity': position,
                                                         'price': best_bid_price, 'action': 'BUY'})


def execute_trade(ticker,ORDER_LIMIT,MAX_LONG_EXPOSURE,MAX_SHORT_EXPOSURE):
    best_bid_price, best_ask_price = get_bid_ask(ticker)
    position = get_position(ticker)
    position1,position2,position3 = get_position('CNR'),get_position('RY'),get_position('AC')
    
    gross_position = abs(position1)+abs(position2)+abs(position3)
    net_position = position1+position2+position3
    spread = best_ask_price - best_bid_price
    spread_capture = math.ceil(spread*100/2.5)/100
    ran_int = 0
    ran_int=random.randint(0,15)
    
  ## if ticker == 'CNR':
    ##    if abs(position1) > 4000:
     ##       if position1> 0:
    ##            clear_all('CNR',position1,best_bid_price,best_ask_price)
     #       else:
     #           clear_all('CNR',position1,best_bid_price,best_ask_price)
     #       continue
                
    
    
    '''if spread > 0.05 and spread < 0.10:
        if gross_position < 20000 and net_position < 20000: #safe zone
            if abs(position) < 4000:
                    print('market makoor')
                    buy_limit(best_bid_price+0.02, ticker, ORDER_LIMIT)
                    buy_sell(best_ask_price-0.02, ticker, ORDER_LIMIT)
            if position > 4000:
                if position > MAX_LONG_EXPOSURE - 10500 : #danger zone
                    buy_sell(best_ask_price-0.01, ticker, ORDER_LIMIT)
                    print('GTFO')
                elif position > MAX_LONG_EXPOSURE:
                    buy_sell(best_ask_price-0.01, ticker, ORDER_LIMIT)
                    print('GTFO RIGHT NOW')
                else: #safe zone
                    print('market makoor')
                    buy_limit(best_bid_price+0.02, ticker, ORDER_LIMIT)
                    buy_sell(best_ask_price-0.02, ticker, ORDER_LIMIT)
            if position < -4000:
                if position < MAX_SHORT_EXPOSURE + 10500 : #danger zone
                    buy_limit(best_bid_price+0.01, ticker, ORDER_LIMIT)
                    print('GTFO')
                elif position < MAX_SHORT_EXPOSURE:
                    buy_limit(best_bid_price+0.01, ticker, ORDER_LIMIT)
                    print('GTFO RIGHT NOW')
                else: #safe zone
                    print('market makoor')
                    buy_limit(best_bid_price+0.02, ticker, ORDER_LIMIT)
                    buy_sell(best_ask_price-0.02, ticker, ORDER_LIMIT)
                    
        else: #gross danger zone
            if position < 0: #short
                buy_limit(best_bid_price, ticker, ORDER_LIMIT*2)
            else: #long
                buy_sell(best_ask_price, ticker, ORDER_LIMIT*2)'''
    if spread >= 0.06:
        if gross_position < 22000 and net_position < 22000: #safe zone
            if abs(position) < 5500:
                    print('huge gap to fill')
                    buy_limit(best_bid_price+spread_capture-0.01, ticker, ORDER_LIMIT*(1+(ran_int/10)))
                    buy_sell(best_ask_price-spread_capture+0.01, ticker, ORDER_LIMIT*(1+(ran_int/10)))
            if position >= 5500:
                if position > MAX_LONG_EXPOSURE - 9500: #danger zone
                    buy_sell(best_ask_price-spread_capture-0.02, ticker, ORDER_LIMIT)
                    sleep(0.1)
                    print('GTFO')
                elif position > MAX_LONG_EXPOSURE:
                    buy_sell(best_ask_price-spread_capture-0.02, ticker, ORDER_LIMIT)
                    sleep(0.1)
                    print('GTFO RIGHT NOW')
                else: #safe zone
                    print('safu')
                    buy_limit(best_bid_price+spread_capture, ticker, ORDER_LIMIT*(1+(ran_int/10)))
                    buy_sell(best_ask_price-spread_capture-0.01, ticker, ORDER_LIMIT*(1+(ran_int/10)))   
            if position <= -5500:
                if position < MAX_SHORT_EXPOSURE + 9500: #danger zone
                    buy_limit(best_bid_price+spread_capture+0.02, ticker, ORDER_LIMIT)
                    sleep(0.1)
                    print('GTFO')
                elif position < MAX_SHORT_EXPOSURE:
                    buy_limit(best_bid_price+spread_capture+0.02, ticker, ORDER_LIMIT)
                    sleep(0.1)
                    print('GTFO RIGHT NOW')
                else: #safe zone
                    print('safu v2')
                    buy_limit(best_bid_price+spread_capture+0.01, ticker, ORDER_LIMIT*(1+(ran_int/10)))
                    buy_sell(best_ask_price-spread_capture, ticker, ORDER_LIMIT*(1+(ran_int/10)))
        else: #gross danger zone
            if position < 0: #short
                buy_limit(best_bid_price, ticker, ORDER_LIMIT*2)
            else: #long
                buy_sell(best_ask_price, ticker, ORDER_LIMIT*2)
    """else:
        if abs(position) > 0:
            print('clear me')
            clear_all(ticker,position,best_bid_price+0.02,best_ask_price-0.02)
            sleep(0.1)"""
            
            
    print('-----------------------------------------')
    print(best_bid_price, best_ask_price)
    print(position)
    print(spread,ticker)
    print('-----------------------------------------')
    sleep(0.1)

def clear_position(position,ticker,ORDER_LIMIT,flag_dict):
    #position = get_position(ticker)
    best_bid_price, best_ask_price = get_bid_ask(ticker)
    
    if position <= -5000:
        size = ORDER_LIMIT if abs(position) > ORDER_LIMIT else position
        print('***************************************')
        print("need to clear:",size)
        print('***************************************')
        buy_limit(best_ask_price-0.03, ticker, size)
        sleep(0.1)
    elif position <= -3500 and position > -5000:
        size = ORDER_LIMIT if abs(position) > ORDER_LIMIT else position
        print('***************************************')
        print("need to clear:",size)
        print('***************************************')
        buy_limit(best_ask_price-0.02, ticker, size)
        sleep(0.1)        
    elif position == 0:
        print('***************************************')
        print("WE HAVE CLEARED!")
        print('***************************************')
        flag_dict[ticker] = False
        sleep(0.1)
    elif position <= 3500:
        size = ORDER_LIMIT if position > ORDER_LIMIT else position
        print('***************************************')
        print("need to sell:",size)
        print('***************************************')
        buy_sell(best_bid_price+0.01, ticker, size)
        sleep(0.1)    
    elif position > 3500 and position <5000:
        size = ORDER_LIMIT if position > ORDER_LIMIT else position
        print('***************************************')
        print("need to sell:",size)
        print('***************************************')
        buy_sell(best_bid_price+0.02, ticker, size)
        sleep(0.1)   
    else:
        size = ORDER_LIMIT if position > ORDER_LIMIT else position
        print('***************************************')
        print("need to sell:",size)
        print('***************************************')
        buy_sell(best_bid_price+0.03, ticker, size)
        sleep(0.1)

def main():
    tick, status = get_tick()
    ticker_list = ['CNR','RY','AC']
    next_cancel = 0
    next_clear = 5
    rolling_neg = 0
    clear_flag = False
    tick_clear_cycle = 5
    flag_dict = {'CNR':False,'RY':False,'AC':False}
    while status == 'ACTIVE':
        for i in range(3):
            print(flag_dict)
            print("TICK",tick,status)
            tick, status = get_tick()
            ticker = ticker_list[i]
            position = get_position(ticker)
            best_bid_price, best_ask_price = get_bid_ask(ticker)
            
            if tick % 2 == 0 and tick != 0: 
                #it is clearing cycle time!
                #check flag though, if flag is True means it is still unloading
                #if flag is False means we need to turn it to True
                if flag_dict[ticker] == True:
                    #continue clearning position
                    clear_position(position,ticker, ORDER_LIMIT,flag_dict)
                else:
                    flag_dict[ticker] = True #set the flag to false
                    #proceed to clearing position
                    clear_position(position,ticker, ORDER_LIMIT,flag_dict)
            
            else:
                #now, we are not in clearing tick
                #but we should still check if the flag is True
                #we only trade if the flag is False
                if position != 0 :
                    # you don't clear 
                    # execute some trades
                    execute_trade(ticker, ORDER_LIMIT, MAX_LONG_EXPOSURE, MAX_SHORT_EXPOSURE)
                    flag_dict[ticker] = False
                    #position is not 0, set the flag back to False for future runs
                else:
                    # check the flag
                    if flag_dict[ticker] == True:
                        #oops, you should still be clearing the position
                        clear_position(position,ticker, ORDER_LIMIT,flag_dict)
                    else:
                        #you are good!
                        execute_trade(ticker, ORDER_LIMIT, MAX_LONG_EXPOSURE, MAX_SHORT_EXPOSURE)
                        flag_dict[ticker] = False
                        #position is not 0, set the flag back to False for future runs
                    

        if next_cancel < tick:
            cancel_all()
            next_cancel = tick + 2
            print('canceled',tick)
      
        
        tick, status = get_tick()
        
        
            
if __name__ == '__main__':
    main()



