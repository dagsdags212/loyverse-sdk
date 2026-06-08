# Endpoints

Every Loyverse resource is reachable as an attribute on a [[Client]]
instance. All endpoints share the same mixin-based interface, so once you know
one you know them all.

## Available endpoints

| Attribute | Resource |
|---|---|
| `client.categories` | Item categories |
| `client.customers` | Customer records |
| `client.discounts` | Discount rules |
| `client.employees` | Staff members |
| `client.inventory` | Stock levels |
| `client.items` | Inventory items |
| `client.merchant` | Merchant account info |
| `client.modifiers` | Item modifiers |
| `client.payment_types` | Payment methods |
| `client.pos_devices` | POS devices |
| `client.receipts` | Transaction receipts |
| `client.shifts` | Employee shifts |
| `client.stores` | Store locations |
| `client.suppliers` | Supplier records |
| `client.taxes` | Tax configurations |
| `client.variants` | Item variants |
| `client.webhooks` | Webhook subscriptions |

Each endpoint exposes the operations supported by the underlying
[Loyverse API](https://developer.loyverse.com/docs/). `merchant` is a singleton
(retrieve only); the rest support listing and, where the API allows, create /
update / delete.

## The CRUD + pagination pattern

| Method | Purpose | Returns |
|---|---|---|
| `await client.X.list(query=None)` | Fetch one page | a list-response model with `.items` and `.next_cursor` |
| `async for r in client.X.iter_all(query=None)` | Stream every page | yields individual model instances |
| `await client.X.retrieve(id)` | Fetch one record | a single model |
| `await client.X.create(payload)` | Create a record | the created model |
| `await client.X.update(id, payload)` | Update a record | the updated model |
| `await client.X.delete(id)` | Delete a record | a deletion result dict |

`list()` and `iter_all()` accept an optional query model — see [[Query-Models]].
The objects returned are Pydantic models documented in [[Models]].

## Worked example: customers

**List with a query model and follow the cursor:**

```python
from loyverse_sdk.models import CustomerListQuery

query = CustomerListQuery(limit=50, email="jane@example.com")
response = await client.customers.list(query)

for customer in response.items:
    print(f"{customer.name} - {customer.email}")

if response.next_cursor:
    next_page = await client.customers.list(
        CustomerListQuery(cursor=response.next_cursor, limit=50)
    )
```

**Retrieve a single record:**

```python
customer = await client.customers.retrieve(id="customer-uuid-here")
print(customer.name, customer.phone_number, customer.address)
```

**Create:**

```python
new_customer = await client.customers.create({
    "name": "Jane Smith",
    "email": "jane@example.com",
    "phone_number": "+1234567890",
    "customer_code": "CUST001",
})
print(f"Created customer: {new_customer.id}")
```

**Update:**

```python
updated = await client.customers.update(
    id=customer.id,
    payload={"email": "newemail@example.com", "note": "VIP customer"},
)
```

**Delete:**

```python
result = await client.customers.delete(id=customer.id)
print(result)  # {'deleted_object_ids': ['customer-uuid']}
```

**Iterate through every record (automatic pagination):**

```python
async for customer in client.customers.iter_all():
    print(customer.name, customer.last_visit)
```

## Streaming vs. paging

Use `iter_all()` when you want to process the entire result set without managing
cursors yourself — it fetches each page lazily and yields one model at a time,
which keeps memory flat for large resources like `receipts`. Use `list()` when
you want a single page or need the `next_cursor` for manual control.

## See also

- [[Client]] — create and configure the client these endpoints hang off
- [[Query-Models]] — every filter available per endpoint
- [[Models]] — the response models returned here
- [[Helpers]] — shortcuts for common receipt queries
- [[Error-Handling]] — what to catch when a call fails
- [[CLI]] — the same operations from the terminal (`loyverse api ...`)
