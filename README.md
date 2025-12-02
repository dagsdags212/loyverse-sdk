# Loyverse API

Asynchronous Python SDK for interacting with the Loyverse API

## Installation

The package utilizes `uv` for local installation.

```
git clone https://github.com/dagsdags212/loyverse_api.git
uv install loyverse_api
```

## Setup

Provide your Loyverse API key as an environment variable named `LOYVERSE_API_KEY`. 
```sh
export LOYVERSE_API_KEY=your_api_key
```

The API key may also be provided in a separate `.env` file located at the root of your project directory.
```.env
LOYVERSE_API_KEY=your_api_key
```

You can also specify the API key in your python script:
```python
import os
os.environ["LOYVERSE_API_KEY"] = "your_api_key"
```

## Usage

**Creating a client**

Create an instance of the `LoyverseClient` to send asynchronous requests to the Loyverse RESTFUL API.
```python
from loyverse_api import LoyverseClient

client = LoyverseClient(api_token=YOUR_API_TOKEN)

# *Perform some operations*

# Close client
await client.close()
```

**Loading API token as an environment variable**

Specify your Loyverse API token in a `.env` file at the project root.
```.env
LOYVERSE_API_TOKEN=your_api_token
```

This will be loaded by a `config` object which can be used to create the client.
```python
from loyverse_api.core.config import config

client = LoyverseClient(api_token=config.LOYVERSE_API_TOKEN)
```

**Retrieving data**

Individual endpoints can be accessed as an attribute of the `LoyverseClient` instance.
Naming conventions are consistent with the paths specified in the [official Loyverse API reference](https://developer.loyverse.com/docs/#tag/Suppliers).

```python
# Fetch customer records
customers = await client.customers.list()

# Fetch receipt records
receipts = await client.receipts.list()

# Fetch employee records
employees = await client.employees.list()
```

**CRUD operations**

Create an item category:
```python
payload = dict(name="Soaps and Detergent", color="BLUE")
new_category = await client.categories.create(payload)

# Returns a pydantic model
print(new_category)
```

```
Category(
    id=UUID('3618d104-cf16-4b65-adce-84f03f71517b'),
    name='Soaps and Detergents',
    color=<CategoryColor.BLUE: 'BLUE'>,
    created_at=datetime.datetime(2025, 11, 29, 23, 35, 26, tzinfo=TzInfo(0)),
    deleted_at=None
)
```

Retrieve the newly created category:
```python
category = await client.categories.retrieve(new_category.id)
```

Update an item category:
```python
payload = dict(color="PURPLE")
updated = await client.categories.update(id=new_category.id, payload=payload)

# Returns the updated model
print(updated)
```

```md
Category(
    id=UUID('a706109e-d589-4a9e-8a71-2b71419fff60'),
    name='Services',
    color=<CategoryColor.PURPLE: 'PURPLE'>,
    created_at=datetime.datetime(2025, 12, 2, 7, 25, 25, 400000, tzinfo=TzInfo(0)),
    deleted_at=None
)
```

Delete an item catgory:
```python
deleted = await client.categories.delete(id=updated.id)
print(deleted)
```

```
{'deleted_object_ids': ['a706109e-d589-4a9e-8a71-2b71419fff60']}
```

**Fetching all records**

The `PaginationMixin` implements cursor-based pagination for retrieving all records from an endpoint.

```python
# Retrieve all customers

async for customer in client.customers.iter_all():
  print(f"{customer.name} first visited on {customer.created_at}")
```

```
John Doe first visited on 2025-09-12 05:40:09+08:00
Micheal Scott first visited on 2025-09-12 05:27:01+08:00
Bart Simpson first visited on 2025-09-12 05:13:48+08:00
Rick Grimes first visited on 2025-09-12 05:09:33+08:00
```
