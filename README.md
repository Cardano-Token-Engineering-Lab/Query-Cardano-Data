# Querying Cardano Native Tokens

There are a lot of various methods for pulling Cardano native token data.  This includes using APIs for various services and products that communicate and send data from a Cardano node. The method that will be used to start off the project will be Blockfrost and Koios' Python API. There are multiple methods for querying data utilizing indexing solutions like db-sync, cardano-graphql, Koios, or Carp and as this repo progresses, different methods of pulling data will be demonstrated.

The documentation to the indexing solutions utilized can be found here [Koios-API-Python](https://github.com/cardano-apexpool/koios-api-python) and here [Blockfrost-Python](https://github.com/blockfrost/blockfrost-python/tree/master) they both enables a simple Python library that connects and pulls data directly from the Koios/Blockfrost to a local machine.

Blockfrost API endpoints can utilized by anyone and has a free-tier available with registration of an account via blockfrost.  Koios for the time being also offers all data for free, but based on updates on their website, it looks like they might scale up services for paid customers in the future.  

Ultimately, the best way to get any data whenever you want would be to spin up a Cardano mainnet node and utilize an indexing solution to query directly from your local node.  Blockfrost offers up a RYO (Run Your Own) service on a local device to be able to query off data indexed by db-sync.  Koios also offers a similar gREST service that can be spun up on a local node as well.  Both are great examples of the Cardano community offering web- and self-hosted solutions.

This section will feature some basic files demonstrating how to utilize the API to begin pulling data into data frames for analysis.  When it comes to modeling the data, further manipulations may be done.

# Future files that will be made are:
1. Holder Distribution Analysis - Understand the breakdown from whales to shrimps
2. Transaction Analysis - Swaps/price/tx frequency and correlations over time
3. Alternative Querying/Indexing Methods for getting Cardano on-chain data
