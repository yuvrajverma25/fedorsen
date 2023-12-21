import re
from django.http import HttpResponse
from django.shortcuts import redirect, render
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from django.contrib.auth.models import User 
from retry import retry
from django.contrib import messages
from myapp.models import AccessCode , AllowedCode
from django.contrib.auth import authenticate, login,logout
from django.contrib.auth.decorators import login_required

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.action_chains import ActionChains


firefox_driver_path = 'geckodriver.exe'

@login_required(login_url='/?message=Please%20enter%20the%20code')
def bets_other(request,country,league,matches,other):
    driver = None
    try:
        # Specify the path to the GeckoDriver executable
        firefox_options = Options()
        firefox_options.add_argument('--headless')

        # Create the Service and WebDriver instances
        driver_service = Service(firefox_driver_path)
        driver = webdriver.Firefox(service=driver_service, options=firefox_options)

        url = f'https://www.oddsportal.com/football/{country}/{league}/{matches}/{other}'

        driver.get(url)
        print('other - ',other)
        print("url - ",url)

        team1 = request.GET.get('team1')
        team2 = request.GET.get('team2')


        WebDriverWait(driver, 5).until(
            EC.presence_of_all_elements_located((By.XPATH, '//*'))
        )

        css_selector = '.border-black-borders.hover\\:bg-gray-light.flex.h-9.cursor-pointer.border-b.border-l.border-r.text-xs'

        # Find all elements matching the CSS selector
        divs = driver.find_elements('css selector', css_selector)

        # Perform actions on each element, if needed
        for div in divs:
            driver.execute_script("arguments[0].click();", div)


        body_element = driver.page_source

        soup = BeautifulSoup(body_element, 'lxml')

        divs = soup.find_all('div','relative flex flex-col')

        # under_div_elements = driver.find_elements(By.CSS_SELECTOR, ".border-black-borders.hover\\:bg-gray-light.flex.h-9.cursor-pointer.border-b.border-l.border-r.text-xs")

        data_list = []

        for div in divs:
            title = div.find('p','max-sm:!hidden')
            ov_ah = div.find_all('p','height-content !text-black-main next-m:min-w-[100%] flex-center min-h-full min-w-[50px] hover:!bg-gray-medium default-odds-bg-bgcolor border gradient-green-added-border')
            
            if title is not None:
                title = title.text.strip()

            over = ov_ah[0].text.strip() if other else ""
            under = ov_ah[1].text.strip() if len(other)>1 else ""
     
            payout = div.find('div','colaps-btn border-black-borders border-l')

            if payout is not None:
                payout = payout.text.strip()

            under_divs_list = []
            uo = div.find('div','flex flex-col')

            try:
                for under_div in uo.find_all('div', class_='border-black-borders flex h-9 border-b border-l border-r text-xs bg-gray-med_light border-black-borders border-b'):
                    under_heading = under_div.find('p', class_='height-content max-mm:hidden pl-4')
                    # handicap = under_div.find('div', class_='border-gray-medium flex min-w-[60px] flex-col items-center justify-center gap-1 border-l text-sm text-[#2F2F2F] max-sm:!hidden max-sm:min-w-[55px]').text.strip()
                    odds = under_div.find_all('p')
                    if len(odds) >= 3:
                        odds1 = odds[1].text.strip()
                        odds2 = odds[2].text.strip()
                    else:
                        # Handle the case where there are not enough 'p' elements
                        odds1 = "N/A"
                        odds2 = "N/A"
                        
                    payout_odds = under_div.find('span', class_='height-content text-[10px]')

                    if payout_odds is not None:
                        payout_odds = payout_odds.text.strip()

                    if under_heading is not None:
                        under_heading = under_heading.text.strip()

                    # Create a dictionary for each under_div
                    under_div_data = {
                        'under_heading': under_heading,
                        'odds1': odds1,
                        'odds2': odds2,
                        'payout': payout_odds
                    }

                    # Append the dictionary to the list
                    under_divs_list.append(under_div_data)

            except Exception as e:
                print("Under div error - ",e)
                return HttpResponse("Error")
            

            bet_data = {
                'title':title,
                'over':over,
                'under':under,
                'payout':payout,
                'under_div':under_divs_list
            }

            data_list.append(bet_data)

        over_under = "#over-under"
        ah = "#ah"
        
        if over_under in other:
            other = over_under
        elif ah in other:
            other = ah
        
        return render(request, 'bets-other.html', {'data_list': data_list,'country':country,'league':league,'matches':matches,'other':other,'team1':team1,'team2':team2})
    
    except Exception as e:
        print("Error" , e)
        return render(request,'error.html')

    finally:
        if driver:
            driver.quit()

def format_odds(input_str):
    # Extract the first decimal point
    first_decimal_index = input_str.find('.')
    
    # Check if there is at least one decimal point
    if first_decimal_index != -1:
        # Extract the substring up to the first decimal point + 3 characters
        formatted_str = input_str[:first_decimal_index + 3]
        return formatted_str
    else:
        # If there is no decimal point, return the original string
        return input_str
    

def inner_data(request,index):
    
    driver = None
    try:
        firefox_options = Options()
        firefox_options.add_argument('--headless')

        # Create the Service and WebDriver instances
        driver_service = Service(firefox_driver_path)
        driver = webdriver.Firefox(service=driver_service, options=firefox_options)

        url = request.GET.get('url',None)
        
        if url is None:
            return Exception
        
        driver.get(url)

        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, '//*'))
        )    

        css_selector = '.flex-center.flex-col.font-bold'

        # Find all elements matching the CSS selector
        divs = driver.find_elements(By.CSS_SELECTOR, css_selector)
        print("DIV length - ", len(divs))

        div = divs[index]

        # driver.execute_script("arguments[0].dispatchEvent(new Event('mouseover'))", div)
        try:
            driver.execute_script("arguments[0].click();", div)

            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, 'flex flex-col gap-2')))
            tool = driver.find_element(By.CSS_SELECTOR,  '.flex.flex-col.gap-2')
            print(tool.text)
            print("Click was successful!")
        except Exception as e :
            print("Timeout: Click may not have been successful.")
            print("Error" , e)
            return render(request,'error.html')

        div_text = div.text
        print("div text = ", div_text)
        print("--------------------------------")
        return HttpResponse("Waao")

    except Exception as e:
        print("Error" , e)
        return render(request,'error.html')

    finally:
        # Close the browser window if the driver is assigned
        if driver:
            driver.quit()




@login_required(login_url='/?message=Please%20enter%20the%20code')
def bets(request,country,league,matches):
    driver = None
    try:
        # Specify the path to the GeckoDriver executable
        firefox_options = Options()
        firefox_options.add_argument('--headless')

        # Create the Service and WebDriver instances
        driver_service = Service(firefox_driver_path)
        driver = webdriver.Firefox(service=driver_service, options=firefox_options)

        tab = request.GET.get('tab',None)

        if tab is not None:
            url = f'https://www.oddsportal.com/football/{country}/{league}/{matches}/{tab}'
        else:
            url = f'https://www.oddsportal.com/football/{country}/{league}/{matches}/#1X2;2'
        
        driver.get(url)
        print("tab - ",tab)
        print("url - ",url)

        team1 = request.GET.get('team1')
        team2 = request.GET.get('team2')
    

        # Wait until the entire DOM is loaded
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, '//*'))
        )        
    
        
        body_element = driver.page_source

        soup = BeautifulSoup(body_element, 'lxml')
        bets = soup.find_all('div','border-black-borders flex h-9 border-b border-l border-r text-xs')
        
        data_list = []
        index = 0

        for bet in bets:
            # print("index - ",index)
            image = bet.find('img', 'bookmaker-logo bg-cover bg-no-repeat')

            if image is not None:
                src = image['src']
                title = image['title']

            odds = bet.find_all('div', 'flex flex-row items-center gap-[3px]')
            # print("Odds length - ",len(odds))
            odds_1 = odds[0].text.strip() if odds else ""
            odds_x = odds[1].text.strip() if len(odds) > 1 else ""
            odds_2 = odds[2].text.strip() if len(odds) > 2 else ""

            odds_1 = format_odds(odds_1)
            odds_2 = format_odds(odds_2)
            odds_x = format_odds(odds_x)
            
            payout = bet.find('span', 'height-content text-[10px]')
            
            if payout is not None:
                payout = payout.text.strip()

            # Create a dictionary for each bet
            bet_data = {
                # 'index_0':index,
                # 'index_1':index + 1,
                # 'index_2':index + 2,
                'src': src,
                'title': title,
                'odds_1': odds_1,
                'odds_x': odds_x,
                'odds_2': odds_2,
                'payout': payout,
            }

            data_list.append(bet_data)
            index = index + 3 
            

        first = "#1X2"
        second = "#bts"

        if tab is not None:
            if first in tab:
                tab = first
            elif second in tab:
                tab = second
        else:
            tab = first

        return render(request, 'bets.html', {'url':url,'data_list': data_list,'country':country,'league':league,'matches':matches,'tab':tab,'team1':team1,'team2':team2})
    

    except Exception as e:
        print("Error" , e)
        return render(request,'error.html')

    finally:
        # Close the browser window if the driver is assigned
        if driver:
            driver.quit()


@login_required(login_url='/?message=Please%20enter%20the%20code')
def football_detail(request,country,league):
    driver = None
    try:
        # Specify the path to the GeckoDriver executable
        firefox_options = Options()
        firefox_options.add_argument('--headless')

        # Create the Service and WebDriver instances
        driver_service = Service(firefox_driver_path)
        driver = webdriver.Firefox(service=driver_service, options=firefox_options)

        url = f'https://www.oddsportal.com/football/{country}/{league}/'

        driver.get(url)

        # Wait until the entire DOM is loaded
        WebDriverWait(driver, 1).until(
            EC.presence_of_all_elements_located((By.XPATH, '//*'))
        )

        body_element = driver.page_source

        soup = BeautifulSoup(body_element, 'lxml')

        country_image= soup.find('div', class_='min-md:items-center max-mt:mt-3 max mt-5 grid w-auto gap-2 px-3')

        # Extract image source and text
        image_src = country_image.find('img')['src']

        main_div = soup.find('div', 'flex flex-col px-3 text-sm max-mm:px-0')

        event_rows = main_div.findAll('div', 'eventRow flex w-full flex-col text-xs')

        data_list = []

        for rows in event_rows:
            date = rows.find('div', 'text-black-main font-main w-full truncate text-xs font-normal leading-5')
            date_str = date.text.strip() if date else ""

            anchor_tag = rows.find('a', 'border-black-borders flex cursor-pointer flex-col border-b')
            href = anchor_tag['href'] if anchor_tag else ""
            time = anchor_tag.find('div', 'flex w-full').text.strip() if anchor_tag else ""

            teams = anchor_tag.findAll('p', 'truncate participant-name') if anchor_tag else []
            team1 = teams[0].text.strip() if teams else ""
            team2 = teams[1].text.strip() if len(teams) > 1 else ""

            odds = anchor_tag.findAll('p', 'height-content !text-black-main next-m:min-w-[100%] flex-center min-h-full min-w-[50px] hover:!bg-gray-medium default-odds-bg-bgcolor border gradient-green-added-border') if anchor_tag else []
            odds_1 = odds[0].text.strip() if odds else ""
            odds_x = odds[1].text.strip() if len(odds) > 1 else ""
            odds_2 = odds[2].text.strip() if len(odds) > 2 else ""

            b = anchor_tag.find('div', 'height-content text-black-main text-[10px] leading-5').text.strip() if anchor_tag else ""

            event_data = {
                'date': date_str,
                'href': href,
                'time': time,
                'team1': team1,
                'team2': team2,
                'odds_1': odds_1,
                'odds_x': odds_x,
                'odds_2': odds_2,
                'additional_info': b
            }

            data_list.append(event_data)

            country = country.upper()
            league = league.upper()

        return render(request, 'football_detail.html', {'data_list': data_list,'image_src':image_src,'country':country,'league':league})

    except Exception as e:
        print(e)
        return HttpResponse(f"Error fetching data from website: {e}")

    finally:
        # Close the browser window if the driver is assigned
        if driver:
            driver.quit()


# Define a function for request handling
def make_request(url):
    headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Error making request to {url}")
    

# Fetch data for home and live function
@retry(tries=3, delay=2, backoff=2, max_delay=40, jitter=(1, 2))
def fetch_rows(url, table_id):
    try:
        response = make_request(url)
        soup = BeautifulSoup(response.text, 'lxml')
        table = soup.select_one(f'#{table_id} table')

        if not table:
            return None

        rows = table.select('tbody tr')
        data = []

        for row in rows:
            cols = row.find_all('td')
            cols_data = {
                'datetime': cols[0].text.strip(),
                'img_src': None,
                'league': cols[2].text.strip(),
                'teams': cols[3].text.strip(),
                'all_money': cols[4].text.strip(),
                'game_id': row.get('game_id'),
            }

            img_tag = cols[1].find('img')
            if img_tag:
                img_src = img_tag.get('src')
                cols_data['img_src'] = urljoin(url, img_src)

            data.append(cols_data)

        return data if data else None

    except RuntimeError:
        return None



# Fetch data for game_detail
@retry(tries=3, delay=2, backoff=2, max_delay=40, jitter=(1, 2))
def fetch_menu(url):
    try:
        response = make_request(url)
        soup = BeautifulSoup(response.text, 'lxml')
        submenu_div = soup.find('div', class_='smenu')

        if not submenu_div:
            return None

        submenu_links = submenu_div.find_all('a', class_='tab')
        submenus = [{'data_tab': link.get('data-tab'), 'text': link.text.strip()} for link in submenu_links]

        return submenus if submenus else None

    except RuntimeError:
        return None



@retry(tries=3, delay=2, backoff=2, max_delay=40, jitter=(1, 2))
def fetch_charts(url, tabContent):
    try:
        response = make_request(url)
        soup = BeautifulSoup(response.text, 'lxml')
        chart_list = []

        tab_content = soup.find('div', {'id': tabContent})

        if not tab_content:
            return None

        charts_items = tab_content.find_all(class_='charts-bk__item')

        if not charts_items:
            return None

        for item in charts_items:
            title = item.find(class_='charts-bk__item-title').text.strip()
            img_src = item.find(class_='charts-bk__item-img').find('img')['src']
            coef = item.find(class_='charts-bk__item-coef').text.strip()

            data = {
                'title': title,
                'img_src': img_src,
                'coef': coef,
            }

            chart_list.append(data)

        return chart_list if chart_list else None

    except RuntimeError:
        return None
    


@retry(tries=3, delay=2, backoff=2, max_delay=40, jitter=(1, 2))
def fetch_tabContent(url, tabContent):
    try:
        response = make_request(url)
        soup = BeautifulSoup(response.text, 'lxml')
        tab_content = soup.find('div', {'id': tabContent})

        if not tab_content:
            return None

        rows = tab_content.select('table tbody tr')
        data = []

        for row in rows:
            cols = row.find_all('td')
            cols_data = {
                'type': cols[0].text.strip(),
                'date': cols[1].text.strip(),
                'market': cols[2].text.strip(),
                'summ': cols[3].text.strip(),
                'change': cols[4].text.strip(),
                'time': cols[5].text.strip(),
                'score': cols[6].text.strip(),
                'odds': cols[7].text.strip(),
                'change_percent': cols[8].text.strip(),
                'all': cols[9].text.strip(),
                'percent_money_on_market': cols[10].text.strip(),
            }
            data.append(cols_data)

        return data if data else None

    except RuntimeError:
        return None
    
@retry(tries=3, delay=2, backoff=2, max_delay=40, jitter=(1, 2))
def fetch_football_rows(url):
    try:
        response = make_request(url)

        soup = BeautifulSoup(response.text, 'lxml')

        sections = soup.find_all('div', class_='flex items-center w-full h-10 gap-1 bg-gray-med_light')

        result_data = []  # List to store dictionaries for each main heading and its list


        for section in sections:
            # Extract the main heading
            main_heading = section.find('span', class_='font-main')
            main_heading_text = main_heading.get_text(strip=True)
            # main = popular,albania ,africa 

            # Find the sibling div with list items
            row_data_list = section.find_next_sibling('div', class_='flex')
            li_elements = row_data_list.find_all('li', class_='flex items-center justify-start w-1/2 h-10 gap-1 pl-3 underline border-b border-r max-sm:w-full border-black-borders')

            # List to store dictionaries for each list item
            li_data_list = []

            for li_element in li_elements:
                a_element = li_element.find('a')
                href_value = a_element['href']
                text_value = a_element.get_text(strip=True)

                li_data_list.append({'href': href_value, 'text': text_value})

            # Create a dictionary for the main heading and its associated list
            main_heading_data = {'main_heading': main_heading_text, 'list_items': li_data_list}

            # Append the dictionary to the result data list
            result_data.append(main_heading_data)

        return result_data

    except Exception as error:
        print(f"An unexpected error occurred: {error}")
        return False


################################################################## Main Functions ###############################################################################################

def home(request):
    url = 'https://www.excapper.com/#premach'
    rows_data = fetch_rows(url, table_id='premach')

    if rows_data is None:
        return redirect('error')

    return render(request, 'home.html', {'rows_data': rows_data})


def live(request):
    url = 'https://www.excapper.com/#live'
    rows_data = fetch_rows(url, table_id='live')

    if rows_data is None:
        return render(request, 'error.html')

    return render(request, 'home.html', {'rows_data': rows_data})

@login_required(login_url='/?message=Please%20enter%20the%20code')
def football_results(request):
    url = 'https://www.oddsportal.com/football/results'

    # Assuming 'rows_data' is intended to store the fetched data
    try:
        rows_data = fetch_football_rows(url)
    except:
        print("oops my error")

    # Pass the data to the template for rendering
    return render(request, 'football.html', {'data': rows_data})


@login_required(login_url='/?message=Please%20enter%20the%20code')
def football(request):
    url = 'https://www.oddsportal.com/football/'

    try:
        rows_data = fetch_football_rows(url)
    except:
        print("oops my error")
        return redirect('error')
    
    if rows_data == False:
        return render(request,'error.html')
    
    return render(request, 'football.html', {'data': rows_data})


def error(request):
    return render(request, 'error.html')


@login_required(login_url='/?message=Please%20enter%20the%20code')
def game_detail(request):
    if request.method == "POST":
        team = request.POST.get('team',None)
        league = request.POST.get('league',None)
        tabContent = request.POST.get('tabContent',None)
        img_src = request.POST.get('img_src',None)
        game_id = request.POST.get('game_id')
        url = f'https://www.excapper.com/?action=game&id={game_id}'
        try:
            menus = fetch_menu(url)

            if tabContent is None and  menus is not None and len(menus) > 0:
                tabContent = menus[0].get('data_tab', tabContent)


            url = f'https://www.excapper.com/?action=game&id={game_id}#{tabContent}'
            chart_urls = fetch_charts(url, tabContent)
            table_rows = fetch_tabContent(url, tabContent)


        except RuntimeError:
            return render(request, 'error.html')

        context = {
            'menus': menus,
            'charts': chart_urls,
            'rows': table_rows,
            'league': league,
            'team': team,
            'img_src': img_src,
            'game_id': game_id,
        }

        return render(request, 'game_detail.html', context)
    
    return redirect('home')



def load_allowed_codes():
    allowed_codes =  AllowedCode.objects.all().values_list('code', flat=True)
    code = list(allowed_codes)
    return code


def check_codes(request):
    AllowedCodes = load_allowed_codes()
    print(AllowedCodes)
   
    if request.method == "POST":
        code_entered = request.POST.get('code')

        # If code is valid
        if code_entered in AllowedCodes:
            access_code = AccessCode.objects.filter(code=code_entered).first()
            #if code is already activated
            if access_code is not None:
                #checking that code is valid or not 
                if access_code.is_valid(): 
                    user = authenticate(request, username=code_entered, password="#$12345") 
                    if user is not None:
                        login(request, user)
                        code = AccessCode.objects.filter(code=code_entered).first()
                        will_expire_on = code.expiration_date
                        messages.success(request,f'Access Granted.Code will expire on-{will_expire_on}')
                        return redirect('home')
                else:
                    messages.warning(request,"Code Expired")
                    if request.user.is_authenticated:
                        logout(request)
                    return redirect('home')
            else:
                try:
                    user = User.objects.create_user(username=code_entered,password="#$12345")
                    code = AccessCode.objects.create(user=user,code=code_entered)
                    code.save()

                    user = authenticate(request, username=code_entered, password="#$12345")
                    if user is not None:
                        login(request, user)
                        will_expire_on = code.expiration_date
                        messages.success(request,f'Access Granted.Code will expire on-{will_expire_on}')
                        return redirect('home')

                except:
                    user = User.objects.filter(f'{code_entered}').first()
                    if user is not None:
                        user.delete()
                        
                    messages.warning(request,"Something went wrong")
                    return redirect('error')
        else:
            messages.warning(request,"Invalid Code")
            return redirect('home')

    return redirect('home')



def logOut(request):
    logout(request)
    return redirect('home')











# css_selector = '.flex-center.flex-col.font-bold'

#         # Find all elements matching the CSS selector
#         divs = driver.find_elements(By.CSS_SELECTOR, css_selector)
#         print("DIV length - ", len(divs))

#         # # Perform actions on each element, if needed
#         for div in divs:

#             # try:
#             #     driver.execute_script("arguments[0].dispatchEvent(new Event('mouseover'))", div)
#             #     # WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, 'tooltip')))
#             #     # tool = driver.find_element(By.CSS_SELECTOR,  'tooltip')
#             #     # print("tool - ",tool.text)
#             #     print("Click was successful!")
#             # except Exception as e :
#             #     print("Timeout: Click may not have been successful.")

#             div_text = div.text
#             print("div text = ", div_text)
#             print("--------------------------------")


def inner(request, index):
    driver = None
    try:
        url = "https://www.oddsportal.com/football/england/premier-league/aston-villa-sheffield-utd-QJsvMDSM/#1X2;2"

        # Set up headless Firefox browser
        firefox_options = Options()
        firefox_options.add_argument('--headless')
        firefox_options.add_argument('--window-size=1013x640')

        driver_service = Service(firefox_driver_path)
        driver = webdriver.Firefox(service=driver_service, options=firefox_options)

        # Navigate to the URL
        driver.get(url)
        print("URL:", url)

        # Find the div element
        css_selector = '.flex-center.flex-col.font-bold'
        divs = driver.find_elements(By.CSS_SELECTOR, css_selector)
        print("Total number of divs:", len(divs))

        if divs:
            # Click the first div
            div = divs[0]
            driver.execute_script("arguments[0].click();", div)

            try:
                # Wait for a new element to appear after the click
                # new_element_selector = '.min-md\\:!hidden.bg-white-main.text-black-main.height-content.border-red-medium.fixed.left-1\\/2.top-1\\/2.z-50.ml-\\[-160px\\].mr-\\[-160px\\].flex.w-\\[320px\\].translate-y-\\[-50%\\].flex-col.border.pb-3.pl-4.pr-4.pt-1.text-xs'
                new_element_selector = '.min-md\\:!hidden'

                new_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, new_element_selector))
                )

                # Print the content of the new element
                print("Content of the new element:", new_element.text)

            except Exception as e:
                # If the timeout occurs, the click was not successful
                print("Click was not successful. Error:", e)

    except Exception as e:
        print("Error:", e)
        return HttpResponse("Error")

    finally:
        # Close the browser window if the driver is assigned
        if driver:
            driver.quit()

    return HttpResponse("Done")