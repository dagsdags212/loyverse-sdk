import asyncio
from loyverse_sdk import LoyverseClient
from loyverse_sdk.models import CustomerListQuery


async def main() -> None:
    client = LoyverseClient()

    await client.export_to_duckdb("cleannest.ddb")
    # query = CustomerListQuery(email="jegsamson13@gmail.com")
    # records = await client.customers.list(query)
    # if records.items:
    #     print(records.items[0])
    # else:
    #     print("No match found!")

    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
