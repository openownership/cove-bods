import os
import time
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

PREFIX_OCDS = os.environ.get('PREFIX_OCDS', '/review/')

BROWSER = os.environ.get('BROWSER', 'ChromeHeadless')


@pytest.fixture(scope='module')
def browser(request):
    if BROWSER == 'ChromeHeadless':
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        browser = webdriver.Chrome(chrome_options=chrome_options)
    else:
        browser = getattr(webdriver, BROWSER)()
    browser.implicitly_wait(3)
    request.addfinalizer(lambda: browser.quit())
    return browser


@pytest.fixture(scope='module')
def server_url(request, live_server):
    if 'CUSTOM_SERVER_URL' in os.environ:
        return os.environ['CUSTOM_SERVER_URL'] + PREFIX_OCDS
    else:
        return live_server.url + PREFIX_OCDS


@pytest.mark.parametrize(('link_text', 'expected_text', 'css_selector', 'url'), [
    ('Open Ownership', 'Anonymous shell companies', '.site-text', 'https://openownership.org/'),
])
def test_footer_ocds(server_url, browser, link_text, expected_text, css_selector, url):
    browser.get(server_url)
    footer = browser.find_element_by_id('footer')
    link = footer.find_element_by_link_text(link_text)
    href = link.get_attribute('href')
    assert url in href
    link.click()
    time.sleep(0.5)
    assert expected_text in browser.find_element_by_css_selector(css_selector).text
