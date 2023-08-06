import pandas as pd

# Token information to be queried and analyzed
policy_id = "da8c30857834c6ae7203935b89278c532b3995245295456f993e1d24"
asset_name = "4c51"
token_name = bytearray.fromhex(asset_name).decode()

project_wallets = {
    "User Distribution": "addr1xx0cj23c0mhfht6uj74x6ytr6c3jr3gnxd3tthdemcxdulrw7xjpplgp0lahw2u869nn77avyd3vw96p4jhtdrykyt4safjps8",
    "Liqwid Team": "addr1x8t020h8h56wrlvs68zee7gps608txntmtxshst0fn0jj8x4nnkuvxxnky367gpfnja0efspn5zlx7a6wvu9wava0l2qwlvsz5",
    "Liqwid Treasury": "addr1xx48fc6r9tl7du7mjx4m6l52a9up2l2gk0vjkdlx5fytlf9eskpm0zchx4z54zlk38w0y7sls2djt9gtmfyef2c4h47snfqcs9",
    "Liqwid Staking": "addr1x8hnww9fyqjq076cqg48qhklyn849daytat3kcxytdhcqvg247jylz4mwn5d7fgjrr70v5wvyz9el7dt5jjswekhuvzq0dmfjq",
    "Liqwid Staking Contract": "addr1w8arvq7j9qlrmt0wpdvpp7h4jr4fmfk8l653p9t907v2nsss7w7r4"
}
