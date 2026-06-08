# Models

Every record the SDK returns is a [Pydantic](https://docs.pydantic.dev/) model:
fields are typed, parsed, and validated, so you get autocomplete and clear errors
instead of raw dictionaries. Models are returned by the
[[Endpoints]] methods and accepted by the exporters.

Import them from `loyverse_sdk.models`:

```python
from loyverse_sdk.models import Receipt, Customer, Item
```

## List responses

List endpoints don't return a bare list — they return a **list-response model**
that wraps the records plus the pagination cursor. Two attributes matter:

| Attribute | Contents |
|---|---|
| `.items` | the list of resource models for this page |
| `.next_cursor` | cursor for the next page, or `None` on the last page |

```python
response = await client.customers.list()

for customer in response.items:      # the records
    print(customer.name)

response.next_cursor                  # feed back into the next query
```

Each resource has its own response model (`CustomerListResponse`,
`ReceiptListResponse`, and so on), but they all expose this same `.items` /
`.next_cursor` shape. `iter_all()` unwraps it for you and yields the individual
models directly — see [[Endpoints]] and [[Query-Models]].

## Resource models

The main models available from `loyverse_sdk.models`:

| Model | Resource |
|---|---|
| `Category` | Item categories |
| `Customer` | Customer records |
| `Discount` | Discount rules |
| `Employee` | Staff members |
| `Inventory` | Stock levels (per variant + store) |
| `Item` | Catalog items |
| `Merchant` | Merchant account profile (singleton) |
| `Modifier` | Item modifiers |
| `PaymentType` | Payment methods |
| `PosDevice` | POS devices |
| `Receipt` | Transaction receipts |
| `Shift` | Employee shifts |
| `Store` | Store locations |
| `Supplier` | Supplier records |
| `Tax` | Tax configurations |
| `Variant` | Item variants |
| `Webhook` | Webhook subscriptions |

Most models inherit common fields — `id`, `created_at`, `updated_at`, and
`deleted_at` — with timestamps parsed to `datetime` and converted to your
configured local timezone.

## Nested structures

Some models embed child structures rather than flat fields. The richest is
`Receipt`, which carries arrays of nested models:

- `line_items` — each `LineItem` has its own `line_taxes`, `line_discounts`, and
  `line_modifiers`
- `payments` — each `Payment` may include `payment_details`
- `total_taxes` and `total_discounts` — receipt-level tax and discount breakdowns

```python
receipt = await client.receipts.retrieve("receipt-uuid")

print(receipt.receipt_number, receipt.total_money)

for line in receipt.line_items:
    print(line.item_name, line.quantity, line.total_money)

for payment in receipt.payments:
    print(payment.type, payment.money_amount)
```

## Accessing fields

Because models are typed, you read fields as attributes:

```python
customer = await client.customers.retrieve("customer-uuid")

print(customer.name)
print(customer.email)
print(customer.total_spent, "across", customer.total_visits, "visits")
```

Models can also carry helper methods. `Customer`, for example, exposes
`tenure()`, which returns the time between a customer's first and last visit:

```python
tenure = customer.tenure()
if tenure:
    print(f"Customer for {tenure.days} days")
```

This page is a reference to the model surface, not an exhaustive field dump — for
the complete list of fields on any model, inspect it in your IDE or call
`Model.model_fields`.

## See also

- [[Endpoints]] — the methods that return these models
- [[Query-Models]] — filter and paginate the list responses
- [[Helpers]] — convenience functions built on top of these models
- [[Flat-File-Export]] — write lists of models straight to CSV or Parquet
- [[Error-Handling]] — `ValidationError` when a response fails to parse
