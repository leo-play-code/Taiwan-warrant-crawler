#http://www.warrantwin.com.tw/eyuanta/Warrant/Search.aspx
import csv 
import os
from selenium.webdriver.support.ui import Select
import concurrent.futures
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
import time
import yfinance as yf

# 權證搜尋,找出單價正常以及
# 股價反推價值配上反推delta和theta
python_path=os.getcwd()+'/data'
def get_option(mode,sell_target):
    '''
    mode (str): 'buy' = 認購權證 or 'sell' = 認售權證
    sell_target (float) = 如果純認售就用'' 如果要對沖認購的部位填寫目標價格
    '''
    # 直接從下載的csv拿資料
    # 獲取頁面中的所有權證資料並且找出優秀的
    def get_data(target):
        # global stock_ex_price
        option = webdriver.ChromeOptions()
        option.add_argument('headless')
        option.add_argument("user-agent=[user-agent string]")
        driver = webdriver.Chrome(python_path+'/chromedriver',chrome_options=option)
        str_target=str(target)
        driver.get('http://www.warrantwin.com.tw/eyuanta/Warrant/Info.aspx?WID='+str_target)
        def name(): # 名稱
            return driver.find_element_by_xpath('/html/body/div[1]/div[2]/div[1]/div/div[4]/div[1]/p[1]/span[2]').text
        def buy_price(): # 買價
            return driver.find_element_by_xpath("/html/body/div[1]/div[2]/div[1]/div/div[4]/div[3]/div/div[2]/div/p[2]").text
        def sell_price(): # 賣價
            return driver.find_element_by_xpath("/html/body/div[1]/div[2]/div[1]/div/div[4]/div[3]/div/div[3]/div/p[2]").text 
        def buy_volume(): # 買量
            return driver.find_element_by_xpath("/html/body/div[1]/div[2]/div[1]/div/div[4]/div[3]/div/div[2]/div/p[3]").text 
        def sell_volume(): #賣量
            return driver.find_element_by_xpath("/html/body/div[1]/div[2]/div[1]/div/div[4]/div[3]/div/div[3]/div/p[3]").text 
        def last_date(): # 行權日
            return driver.find_element_by_xpath("/html/body/div[1]/div[2]/div[1]/div/div[5]/div/ul[1]/li[2]/span[2]").text 
        def outside_volume(): # 流通比例
            ans=driver.find_element_by_xpath("/html/body/div[1]/div[2]/div[1]/div/div[5]/div/ul[1]/li[6]/span[2]").text 
            ans=ans.split('/')
            if '--%' in ans[1]:
                ans[1]='0.00%'
            return ans[1]
        def end_price(): # 履約價
            return float(driver.find_element_by_xpath("/html/body/div[1]/div[2]/div[1]/div/div[5]/div/ul[1]/li[7]/span[2]").text)
        def rate(): # 行使比例
            return driver.find_element_by_xpath("/html/body/div[1]/div[2]/div[1]/div/div[5]/div/ul[1]/li[8]/span[2]").text 
        def theta(): # theta
            return driver.find_element_by_xpath("/html/body/div[1]/div[2]/div[1]/div/div[5]/div/ul[2]/li[4]/span[2]").text 
        def delta(): # theta
            return driver.find_element_by_xpath('/html/body/div[1]/div[2]/div[1]/div/div[5]/div/ul[2]/li[3]/span[2]').text 
        def day_later(): # 剩餘日
            return driver.find_element_by_xpath("/html/body/div[1]/div[2]/div[1]/div/div[5]/div/ul[2]/li[5]/span[2]").text 
        def lever(): # 槓桿
            return driver.find_element_by_xpath("/html/body/div[1]/div[2]/div[1]/div/div[5]/div/ul[2]/li[7]/span[2]").text
        def price_rate(): # 買賣價差比
            return driver.find_element_by_xpath("/html/body/div[1]/div[2]/div[1]/div/div[5]/div/ul[2]/li[8]/span[2]").text 
        price_rate_div=float(str((price_rate())).replace('%',''))
        data = yf.download(tickers='^TWII', period='1d', interval='1d')
        i=0
        while i<len(data):
            close_price=data.Close[i]
            i+=1
        if mode=='buy':
            double_up=round(float(buy_price())/float(delta())-(float(theta())*30)/float(delta()),0)
            print('before',double_up,end_price(),close_price,end_price()/close_price)
            double_up=round(double_up*(end_price()/close_price))
            print('after',double_up)
            if price_rate_div/float(lever()) <=0.3:
                temp_lever=round(price_rate_div/float(lever()),2)
                # 時間損失率越大越不好
                theta_delta=round(float(theta())/float(delta()))
                rateofprice=round((float(delta())/float(buy_price()))*100,5)
                # if double_up<=2000:
                with open(python_path+"/權證buy.csv","a") as fd:
                    writer = csv.writer(fd)
                    writer.writerow([target,name(),buy_price(),sell_price(),outside_volume(),round(end_price(),2),rate(),theta(),delta(),day_later(),lever(),price_rate(),temp_lever,theta_delta,rateofprice,double_up])
                # else:
                #     print('not good enough')
        elif mode=='sell':
            double_up=round(float(buy_price())/float(delta())*(-1)+(float(theta())*30)/float(delta()),0)
            double_up=round(double_up*(close_price/end_price()))
            temp_lever=round(price_rate_div/float(lever()),2)
            # 時間損失率越大越不好
            theta_delta=round(float(theta())/float(delta()))
            rateofprice=round((float(delta())/float(buy_price()))*100,5)
            if sell_target=='':
                if theta_delta<=20 and temp_lever>=-0.3: 
                    if double_up<=2200:
                        with open(python_path+"/權證sell.csv","a") as fd:
                            writer = csv.writer(fd)
                            writer.writerow([target,name(),buy_price(),sell_price(),outside_volume(),round(end_price(),2),rate(),theta(),delta(),day_later(),lever(),price_rate(),temp_lever,theta_delta,rateofprice,double_up])
                    # else:
                    #     print('not good enough')
            else:
                # 找出成本最低,效益最好的對沖(時間損失率低,槓桿大or比例大),再利用delta來推要買幾張成本
                if theta_delta<=20 and temp_lever>=-0.3: 
                    if double_up<=2200:
                        money_all=round((sell_target/(float(delta())*(-1)*10000))*float(sell_price())*1000)
                        with open(python_path+"/權證對沖.csv","a") as fd:
                            writer = csv.writer(fd)
                            writer.writerow([target,name(),buy_price(),sell_price(),outside_volume(),round(end_price(),2),rate(),theta(),delta(),day_later(),lever(),price_rate(),temp_lever,theta_delta,rateofprice,money_all,double_up])
        driver.quit()
    # 輸入要追蹤的股票代號並且找出權證
    def search(ticker):
        ticker=str(ticker)
        back=0
        while back<10:
            driver.find_element_by_xpath('/html/body/div[1]/div[2]/div[1]/div/div[1]/div[1]/div[1]/div[1]/table/tbody/tr[1]/td/div/input').send_keys(Keys.BACKSPACE)
            back+=1
        time.sleep(3)
        driver.find_element_by_xpath('/html/body/div[1]/div[2]/div[1]/div/div[1]/div[1]/div[1]/div[1]/table/tbody/tr[1]/td/div/input').send_keys(ticker)
        # wait.until(EC.visibility_of_element_located((By.CLASS_NAME,'ng-isolate-scope.searchInput')))
        time.sleep(2)
        if 'TWT' in ticker:
            for i in range(10):
                if i!=0:
                    if '臺股指數' in driver.find_element_by_xpath('/html/body/div[1]/div[2]/div[1]/div/div[1]/div[1]/div[1]/div[1]/table/tbody/tr[1]/td/div/ul/li['+str(i)+']/a').text:
                        driver.find_element_by_xpath('/html/body/div[1]/div[2]/div[1]/div/div[1]/div[1]/div[1]/div[1]/table/tbody/tr[1]/td/div/ul/li['+str(i)+']/a').click()
                        break
        else:
            try:
                driver.find_element_by_xpath('/html/body/div[1]/div[2]/div[1]/div/div[1]/div[1]/div[1]/div[1]/table/tbody/tr[1]/td/div/ul/li[1]/a').click()
            except:
                return False
        # 選擇權證購or售
        select_option=driver.find_element_by_xpath('//*[@id="mm-0"]/div[2]/div[1]/div/div[1]/div[1]/div[1]/div[1]/table/tbody/tr[2]/td/div/select')
        select = Select(select_option)
        if mode=='buy':
            select.select_by_visible_text('認購')
        elif mode=='sell':
            select.select_by_visible_text('認售')
        time.sleep(1)
        # sell
        # select.select_by_visible_text('認售')
        # 選擇券商
        select_seller_option=driver.find_element_by_xpath('//*[@id="mm-0"]/div[2]/div[1]/div/div[1]/div[1]/div[1]/div[1]/table/tbody/tr[3]/td/div/select')
        select_seller=Select(select_seller_option)
        select_seller.select_by_visible_text('元大證券')
        time.sleep(1)
        # 選擇時間
        select_day_option=driver.find_element_by_xpath('//*[@id="mm-0"]/div[2]/div[1]/div/div[1]/div[1]/div[1]/div[2]/table/tbody/tr[5]/td/div/select[1]')
        select_day=Select(select_day_option)
        if mode=='buy':
            select_day.select_by_visible_text('180日')
        elif mode=='sell':
            select_day.select_by_visible_text('90日')
        time.sleep(1)
        # 搜尋
        driver.find_element_by_xpath('/html/body/div[1]/div[2]/div[1]/div/div[1]/div[1]/div[2]/a[2]').click()    
        time.sleep(1)
    url='http://www.warrantwin.com.tw/eyuanta/Warrant/Search.aspx'
    option = webdriver.ChromeOptions()
    option.add_argument('headless')
    option.add_argument("user-agent=[user-agent string]")
    driver = webdriver.Chrome(python_path+'/chromedriver',chrome_options=option)
    driver.get(url)
    wait=WebDriverWait(driver,10)
    # 想測試的權證加入list
    stock=['TWT']
    stock_id_box=[]
    for item in stock:
        if search(item) == False:
            continue
        else:
            pass
        time.sleep(1)
        total=int(driver.find_element_by_xpath('/html/body/div[1]/div[2]/div[1]/div/div[2]/div/p/label[2]').text)
        k_final=int(total/20)
        left_k=total%20
        if left_k !=0:
            k=1
            while k<=k_final:
                i=2
                while i<=21:
                    str_i=str(i)
                    web='/html/body/div[1]/div[2]/div[1]/div/div[2]/div/div[2]/table/tbody/tr['+str_i+']/td[2]/div/a'
                    stock_id=driver.find_element_by_xpath(web).text
                    stock_id_box.append(stock_id)
                    i+=1
                if k_final<5:
                    if left_k !=0:
                        k_final_num=k_final+1
                    else:
                        k_final_num=k_final
                    num_next_page=2+k_final_num+1
                    str_next_page=str(num_next_page)
                    driver.find_element_by_xpath('/html/body/div[1]/div[2]/div[1]/div/div[4]/ul/li['+str_next_page+']/a').click()
                else:
                    driver.find_element_by_xpath('/html/body/div[1]/div[2]/div[1]/div/div[4]/ul/li[8]/a').click()
                time.sleep(1)
                k+=1
            i=2
            while i<=left_k+1:
                str_i=str(i)
                web='/html/body/div[1]/div[2]/div[1]/div/div[2]/div/div[2]/table/tbody/tr['+str_i+']/td[2]/div/a'
                stock_id=driver.find_element_by_xpath(web).text
                stock_id_box.append(stock_id)
                i+=1
        else:
            k=0
            while k<=k_final:
                i=2
                while i<=21:
                    str_i=str(i)
                    web='/html/body/div[1]/div[2]/div[1]/div/div[2]/div/div[2]/table/tbody/tr['+str_i+']/td[2]/div/a'
                    stock_id=driver.find_element_by_xpath(web).text
                    stock_id_box.append(stock_id)
                    i+=1
                if k_final<5:
                    if left_k !=0:
                        k_final_num=k_final+1
                    else:
                        k_final_num=k_final
                    num_next_page=2+k_final_num+1
                    str_next_page=str(num_next_page)
                    driver.find_element_by_xpath('/html/body/div[1]/div[2]/div[1]/div/div[4]/ul/li['+str_next_page+']/a').click()
                else:
                    driver.find_element_by_xpath('/html/body/div[1]/div[2]/div[1]/div/div[4]/ul/li[8]/a').click()
                time.sleep(1)
                k+=1
        time.sleep(5)
    driver.quit()
    i=0
    try:
        if mode=='buy':
            os.remove(python_path+"/權證buy.csv")
        elif mode=='sell':
            if sell_target=='':
                os.remove(python_path+"/權證sell.csv")
            else :
                os.remove(python_path+"/權證對沖.csv")
    except:
        pass
    if mode=='buy':
        with open(python_path+"/權證buy.csv","a") as fd:
            writer = csv.writer(fd)
            writer.writerow(['代號','名稱','買價','賣價','流通比例','履約價','行使比例','theta','delta','剩餘日','實質槓桿','價差比','差槓比','時間損失率','比例','翻倍率'])
    elif mode=='sell':
        if sell_target=='':
            with open(python_path+"/權證sell.csv","a") as fd:
                writer = csv.writer(fd)
                writer.writerow(['代號','名稱','買價','賣價','流通比例','履約價','行使比例','theta','delta','剩餘日','實質槓桿','價差比','差槓比','時間損失率','比例','翻倍率'])
        else:
            with open(python_path+"/權證對沖.csv","a") as fd:
                writer = csv.writer(fd)
                writer.writerow(['代號','名稱','買價','賣價','流通比例','履約價','行使比例','theta','delta','剩餘日','實質槓桿','價差比','差槓比','時間損失率','比例','資金','翻倍率'])
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(get_data, stock_id_box)



