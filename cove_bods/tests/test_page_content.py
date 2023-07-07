import pytest

from libcoveweb2.tests.lib_functional import browser, server_url  # noqa

from selenium.webdriver.common.by import By


@pytest.mark.parametrize(
    ("link_text", "url"),
    [
        (
            "Beneficial Ownership Data Standard",
            "http://standard.openownership.org/",
        ),
    ],
)
def test_footer_bods(server_url, browser, link_text, url):  # noqa
    browser.get(server_url)
    footer = browser.find_element(By.ID, "footer")
    link = footer.find_element(By.LINK_TEXT, link_text)
    href = link.get_attribute("href")
    assert href == url
