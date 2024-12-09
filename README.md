# auto-batch

Faster Anvil Data Tables via batching, without the boilerplate. 

By default, each [Anvil Data Table](https://anvil.works/docs/data-tables#using-data-tables-from-python) operation (with the exception of accessing cached information) makes a separate round-trip to the database, which takes on the order of 0.02 seconds. If you are looping through dozens or hundreds of row updates, deletes, or additions, that can add up to noticeable lags. (Moreover, within [a transaction](https://anvil.works/docs/data-tables/transactions#using-a-decorator), longer execution times are compounded by increasing the likelihood of conflicts triggering one or more re-tries of the entire transaction.) The [Accelerated Tables Beta](https://anvil.works/docs/data-tables/accelerated-tables#new-features) allows you to batch add, update, and delete rows and thus condense many Data Tables operations to a single round trip to the database. But doing so requires changes to your code (even when the Data Table operations are within a transaction, which implies they are meant to be executed together as a block). For example:

```python
import anvil.tables as tables

@tables.in_transaction
def update_cache():
    now = utcnow()
    rows = tables.app_tables.table_1.search()
    with tables.batch_update, tables.batch_delete:                 # batch refactor
        new_log_rows = []                                          # batch refactor
        for row in rows:
            if row['expire_dt'] < now:
                row.delete()
            elif row['next_update_dt'] < now:
                row['next_update_dt'] = now + timedelta(minutes=30)
                new_log_rows.append(dict(id=row['id'], date=now))  # batch refactor
    tables.app_tables.update_log.add_rows(new_log_rows)            # batch refactor
```

With auto-batch, you get the same performance gains without changing your code, aside from subbing in `auto_batch.tables` for `anvil.tables`:

```python
from auto_batch import tables

@tables.in_transaction
def update_cache():
    now = utcnow()
    rows = tables.app_tables.table_1.search()
    print(f"Table 1 has {len(rows)} rows.")
    for row in rows:
        if row['expire_dt'] < now:
            row.delete()
        elif row['next_update_dt'] < now:
            row['next_update_dt'] = now + timedelta(minutes=30)
            tables.app_tables.update_log.add_row(id=row['id'], date=now)
```

However, auto-batch is not yet production-ready. Use at your own risk. Help in development (and especially writing a comprehensive test suite) welcomed!

## Setup

* Ensure that you have [enabled Accelerated Tables](https://anvil.works/docs/data-tables/accelerated-tables#enabling-the-accelerated-tables-beta) for your app.
* Add auto-batch to your app as a [third-party dependency](https://anvil.works/forum/t/third-party-dependencies/8712) with the token `PKF2MZRQMPCXFWNE`.

## Usage

Use `auto_batch.tables` any place you would use `anvil.tables`, as well as `auto_batch.users` in places of `anvil.users` so that `get_user` and `force_login` work with auto-batch's wrapped Table rows. Table operations within transactions will then be batched automatically. To batch adds, updates, and deletes outside of transactions, you can use the `AutoBatch` context manager:

```python
with auto_batch.tables.AutoBatch():
    ...
```

Unfortunately, some Tables functionality is not yet supported. Otherwise, if you only supported features, auto-batch should work as a plug-in substitute for anvil.tables in your app:

- [anvil.tables](https://anvil.works/docs/api/anvil.tables)
  - [x] `app_tables`  
  - [x] Exceptions
  - [x] Functions (esp. `in_transaction`)
  - [x] `Row`
  - `SearchIterator`
    - [ ] `to_csv`
  - `Table`
    - [x] `add_row`
    - [x] `add_rows` 
    - [ ] `client_readable`
    - [ ] `client_writeable`
    - [ ] `client_writeable_cascase`
    - [x] `delete_all_rows`
    - [x] `get`
    - [x] `get_by_id`
    - [ ] `has_row`
    - [x] `list_columns`
    - [x] `search`
    - [ ] `to_csv`
  - [x] `Transaction`
- [x] [anvil.tables.query](https://anvil.works/docs/api/anvil.tables.query)
- [x] [anvil.users](https://anvil.works/docs/api/anvil.users)


### Built With

* [Anvil](https://anvil.works) - web apps built entirely with Python (See below for more.)

### License

This project is licensed under the MIT License - see the [LICENSE](LICENSE.txt) file for details.

---

## Using Anvil to edit this app

The app in this repository is built with [Anvil](https://anvil.works?utm_source=github:app_README), the framework for building web apps with nothing but Python. You can clone this app into your own Anvil account to test and modify.

First, fork this repository to your own GitHub user account. Click on the top right of this repo to fork it to your own account.

### Syncing your fork to the Anvil Editor

Then go to the [Anvil Editor](https://anvil.works/build?utm_source=github:app_README) (you might need to sign up for a free account) and click on “Clone from GitHub” (underneath the “Blank App” option):

<img src="https://anvil.works/docs/version-control-new-ide/img/git/clone-from-github.png" alt="Clone from GitHub"/>

Enter the URL of your forked GitHub repository. If you're not yet logged in, choose "GitHub credentials" as the authentication method and click "Connect to GitHub".

<img src="https://anvil.works/docs/version-control-new-ide/img/git/clone-app-from-git.png" alt="Clone App from Git modal"/>

Finally, click "Clone App".

The app will then be in your Anvil account, ready for you to run it or start editing it! **Any changes you make will be automatically pushed back to your fork of this repository, if you have permission!** You might want to [make a new branch](https://anvil.works/docs/version-control-new-ide?utm_source=github:app_README).

### Running the app yourself:

Find the **Run** button at the top-right of the Anvil editor:

<img src="https://anvil.works/docs/img/run-button-new-ide.png"/>

## More about Anvil

If you’re new to Anvil, welcome! Anvil is a platform for building full-stack web apps with nothing but Python. No need to wrestle with JS, HTML, CSS, Python, SQL and all their frameworks – just build it all in Python.

<figure>
<figcaption><h3>Learn About Anvil In 80 Seconds👇</h3></figcaption>
<a href="https://www.youtube.com/watch?v=3V-3g1mQ5GY" target="_blank">
<img
  src="https://anvil-website-static.s3.eu-west-2.amazonaws.com/anvil-in-80-seconds-YouTube.png"
  alt="Anvil In 80 Seconds"
/>
</a>
</figure>
<br><br>

[![Try Anvil Free](https://anvil-website-static.s3.eu-west-2.amazonaws.com/mark-complete.png)](https://anvil.works?utm_source=github:app_README)

To learn more about Anvil, visit [https://anvil.works](https://anvil.works?utm_source=github:app_README).

### Tutorials

If you are just starting out with Anvil, why not **[try the 10-minute Feedback Form tutorial](https://anvil.works/learn/tutorials/feedback-form?utm_source=github:app_README)**? It features step-by-step tutorials that will introduce you to the most important parts of Anvil.

Anvil also has tutorials on:
- [Multi-User Applications](https://anvil.works/learn/tutorials/multi-user-apps?utm_source=github:app_README)
- And [much more....](https://anvil.works/learn/tutorials?utm_source=github:app_README)

### Reference Documentation

The Anvil reference documentation provides comprehensive information on how to use Anvil to build web applications. You can find the documentation [here](https://anvil.works/docs/overview?utm_source=github:app_README).

If you want to get to the basics as quickly as possible, each section of this documentation features a [Quick-Start Guide](https://anvil.works/docs/overview/quickstarts?utm_source=github:app_README).
