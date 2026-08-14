import asyncio
import json
import os

from playwright.async_api import async_playwright


WORKFLOW_PATH = (
    "outputs/json_generation/sample_json.json"
)


async def execute_workflow(workflow):

    async with async_playwright() as p:

        # Launch browser
        browser = await p.chromium.launch(
            headless=False
        )

        page = await browser.new_page()

        # CRM path
        crm_path = os.path.abspath(
            "automation/crm.html"
        )

        crm_url = (
            "file:///"
            + crm_path.replace("\\", "/")
        )

        print("\nStarting workflow execution...\n")

        # ---------------------------------
        # Execute workflow steps
        # ---------------------------------

        for step in workflow.get(
            "steps",
            []
        ):

            action = step.get(
                "action",
                ""
            )

            target = step.get(
                "target",
                ""
            )

            value = step.get(
                "value",
                ""
            )

            print(
                f"Executing: "
                f"{action} -> {target}"
            )

            # ---------------------------------
            # OPEN PAGE
            # ---------------------------------

            if action == "OPEN_PAGE":

                await page.goto(
                    crm_url
                )

                await page.wait_for_load_state(
                    "domcontentloaded"
                )

            # ---------------------------------
            # CLICK
            # ---------------------------------

            elif action == "CLICK":

                if target in [
                    "Add Customer",
                    "add-customer"
                ]:

                    await page.get_by_role(
                        "button",
                        name="Add Customer"
                    ).click()

            # ---------------------------------
            # ENTER TEXT
            # ---------------------------------

            elif action == "ENTER_TEXT":

                if target in [
                    "Customer Name",
                    "customer-name"
                ]:

                    await page.locator(
                        "#customerName"
                    ).fill(value)

                elif target in [
                    "Phone Number",
                    "phone-number"
                ]:

                    await page.locator(
                        "#phoneNumber"
                    ).fill(value)

            # ---------------------------------
            # READ TABLE
            # ---------------------------------

            elif action == "READ_TABLE":

                rows = await page.locator(
                    "#customerTableBody tr"
                ).all()

                customers = []

                for row in rows:

                    cells = await row.locator(
                        "td"
                    ).all_text_contents()

                    if len(cells) >= 2:

                        customers.append({
                            "name": cells[0].strip(),
                            "phone": cells[1].strip()
                        })

                print(
                    "\nCustomer Table:"
                )

                print(
                    json.dumps(
                        customers,
                        indent=4
                    )
                )

                # Expected verification values
                expected_name = workflow.get(
                    "verify_name",
                    ""
                )

                expected_phone = workflow.get(
                    "verify_phone",
                    ""
                )

                # Verify customer
                verified = any(
                    customer["name"]
                    == expected_name
                    and
                    customer["phone"]
                    == expected_phone
                    for customer in customers
                )

                if verified:

                    print(
                        "\nVerification: "
                        "SUCCESS ✅"
                    )

                else:

                    print(
                        "\nVerification: "
                        "FAILED ❌"
                    )

            # ---------------------------------
            # WAIT
            # ---------------------------------

            elif action == "WAIT":

                wait_time = int(
                    value or 1000
                )

                await page.wait_for_timeout(
                    wait_time
                )

            # ---------------------------------
            # SCROLL
            # ---------------------------------

            elif action == "SCROLL":

                await page.mouse.wheel(
                    0,
                    600
                )

            # ---------------------------------
            # TAKE SCREENSHOT
            # ---------------------------------

            elif action == "TAKE_SCREENSHOT":

                os.makedirs(
                    "screenshots",
                    exist_ok=True
                )

                await page.screenshot(
                    path=(
                        "screenshots/"
                        "automation_result.png"
                    ),
                    full_page=True
                )

                print(
                    "Screenshot saved."
                )

            # ---------------------------------
            # Unsupported action
            # ---------------------------------

            else:

                print(
                    f"Unsupported action: "
                    f"{action}"
                )

        print(
            "\nWorkflow execution completed."
        )

        # Keep browser open for testing
        input(
            "\nPress ENTER to close the browser..."
        )

        await browser.close()


# ---------------------------------
# Main
# ---------------------------------

if __name__ == "__main__":

    if not os.path.exists(
        WORKFLOW_PATH
    ):

        print(
            "\nERROR: Workflow JSON "
            "not found."
        )

        print(
            f"Expected file: "
            f"{WORKFLOW_PATH}"
        )

        print(
            "\nFirst run:"
        )

        print(
            "python app/core/json_generator.py"
        )

        exit()

    # Load generated workflow
    with open(
        WORKFLOW_PATH,
        "r",
        encoding="utf-8"
    ) as file:

        workflow = json.load(file)

    print(
        "\nLoaded AI-generated workflow:"
    )

    print(
        json.dumps(
            workflow,
            indent=4
        )
    )

    asyncio.run(
        execute_workflow(
            workflow
        )
    )