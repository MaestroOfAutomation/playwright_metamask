import asyncio
from playwright.async_api import async_playwright, Page, Playwright
from mnemonic import Mnemonic

path_to_extension = "./MetaMask-Chrome_2"
user_data_dir = "/tmp/test-user-data-dir"

mnemo = Mnemonic("english")

def get_random_seed_phrase() -> list[str]:
    phrase_string = mnemo.generate(strength=128)

    return phrase_string.split(' ')


async def run(playwright: Playwright):
    context = await playwright.chromium.launch_persistent_context(
        user_data_dir,
        headless=False,
        args=[
            f"--disable-extensions-except={path_to_extension}",
            f"--load-extension={path_to_extension}",
        ],
    )

    page: Page = await context.new_page()
    await page.goto('chrome://extensions')

    extension_id_by_name: dict[str, str] = {}

    card_elements = await page.query_selector_all(selector='div#card')
    for card in card_elements:
        name_element = await card.query_selector(selector='div#name')
        name: str = await name_element.text_content()

        details_element = await card.query_selector(selector='cr-button#detailsButton')

        async with page.expect_navigation():
            await details_element.click()

        # chrome://extensions/?id=ognblmgeejlfffffeidmmmjjmginlfga
        url: str = page.url
        extension_id: str = url.split('?id=')[-1]
        print(name, extension_id)

        extension_id_by_name[name] = extension_id

        back_button = await page.query_selector(selector='cr-icon-button#closeButton')
        async with page.expect_navigation():
            await back_button.click()

    metamask_extension_id: str = extension_id_by_name['MetaMask']

    await page.goto(
        url=f'chrome-extension://{metamask_extension_id}/home.html#onboarding/welcome',
    )

    terms_checkbox = page.get_by_test_id('onboarding-terms-checkbox')
    await terms_checkbox.click()

    import_wallet_button = page.get_by_test_id('onboarding-import-wallet')
    await import_wallet_button.click()

    no_thanks_button = page.get_by_test_id('metametrics-no-thanks')
    await no_thanks_button.click()

    random_seed: list[str] = get_random_seed_phrase()

    for idx in range(12):
        input_element = page.get_by_test_id(f'import-srp__srp-word-{idx}')
        await input_element.fill(value=random_seed[idx])

    confirm_button = page.get_by_test_id('import-srp-confirm')
    await confirm_button.click()

    password = 'Megatestpassword'

    for test_id in ('create-password-new', 'create-password-confirm'):
        input_element = page.get_by_test_id(test_id)
        await input_element.fill(value=password)

    confirm_button = page.get_by_test_id('create-password-terms')
    await confirm_button.click()

    import_button = page.get_by_test_id('create-password-import')
    await import_button.click()

    done_button = page.get_by_test_id('onboarding-complete-done')
    await done_button.click()

    next_button = page.get_by_test_id('pin-extension-next')
    await next_button.click()

    done_button = page.get_by_test_id('pin-extension-done')
    await done_button.click()

    owlto_page = await context.new_page()
    await owlto_page.goto('https://owlto.finance/')

    connect_wallet_button = owlto_page.get_by_text(' Connect Wallet ').first
    await connect_wallet_button.click()

    metamask_button = owlto_page.get_by_text('MetaMask', exact=True).first
    await metamask_button.click()

    await asyncio.sleep(3)

    metamask_page: Page | None = None

    for _page in context.pages:
        url: str = _page.url
        if f'{metamask_extension_id}/notification.html' in url:
            metamask_page = _page
            break

    if metamask_page is None:
        raise RuntimeError('Could not find metamask extension')

    await metamask_page.get_by_test_id('confirm-btn').click()

    await asyncio.Future()

    await context.close()


async def main():
    async with async_playwright() as playwright:
        await run(playwright)

if __name__ == '__main__':
    asyncio.run(main())