import koios_python
from datetime import datetime, timedelta
from collections import defaultdict
import pandas as pd
from typing import Dict, Set, List
import logging
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CardanoHIndex:
    def __init__(self, koios_url: str = "http://10.0.0.89:8053/api/v1/"):
        """Initialize with Koios endpoint"""
        self.koios = koios_python.URLs(url=koios_url)

    def get_block_range(self, days: int) -> List[dict]:
        """Get blocks for the specified number of days"""
        try:
            # Get current tip
            tip = self.koios.get_tip()
            current_block_height = tip[0]["block_no"]

            # Estimate blocks to fetch (assuming ~20 second block time)
            blocks_per_day = 24 * 60 * 60 // 20
            blocks_needed = blocks_per_day * days

            # Fetch blocks in batches
            all_blocks = []
            batch_size = 1000  # Maximum allowed by the API

            for start_idx in range(0, blocks_needed, batch_size):
                # Calculate the range for this batch
                end_idx = min(start_idx + batch_size - 1, blocks_needed - 1)
                content_range = f"{start_idx}-{end_idx}"

                logger.info(f"Fetching blocks range: {content_range}")
                blocks = self.koios.get_blocks(content_range=content_range)

                if not blocks:  # If no blocks returned, we've reached the end
                    break

                all_blocks.extend(blocks)

                # Add a small delay to avoid overwhelming the node
                time.sleep(0.1)

            logger.info(f"Retrieved {len(all_blocks)} blocks total")
            return all_blocks

        except Exception as e:
            logger.error(f"Error fetching blocks: {e}")
            raise

    def get_block_transactions(self, block_hash: str) -> List[dict]:
        """Get transactions for a specific block"""
        try:
            txs = self.koios.get_block_txs(block_hash)
            return txs
        except Exception as e:
            logger.error(f"Error fetching transactions for block {block_hash}: {e}")
            return []

    def calculate_daily_h_index(self, receiver_senders: Dict[str, Set[str]]) -> int:
        """
        Calculate h-index based on the number of receivers with at least h unique senders
        """
        # Get count of unique senders for each receiver
        sender_counts = sorted(
            [len(senders) for senders in receiver_senders.values()], reverse=True
        )

        h_index = 0
        for i, count in enumerate(sender_counts, 1):
            if count >= i:
                h_index = i
            else:
                break

        return h_index

    def process_block_transactions(self, block: dict) -> Dict[str, Set[str]]:
        """Process all transactions in a block to get receiver-sender relationships"""
        receiver_senders = defaultdict(set)

        # Get transactions for this block
        txs = self.get_block_transactions(block["hash"])

        if not txs:
            return receiver_senders

        # Process transactions in batches of 10
        BATCH_SIZE = 10
        tx_hashes = [tx["tx_hash"] for tx in txs]

        for i in range(0, len(tx_hashes), BATCH_SIZE):
            batch_hashes = tx_hashes[i : i + BATCH_SIZE]
            try:
                # Get detailed transaction information for the batch
                tx_infos = self.koios.get_tx_info(*batch_hashes)

                if not tx_infos:
                    continue

                for tx_detail in tx_infos:
                    # Extract sender addresses from inputs
                    sender_addresses = set()
                    if "inputs" in tx_detail:
                        for tx_input in tx_detail["inputs"]:
                            if isinstance(tx_input, dict) and "payment_addr" in tx_input:
                                sender_addresses.add(tx_input["payment_addr"]["bech32"])

                    # Handle outputs and update receiver_senders
                    if "outputs" in tx_detail:
                        for output in tx_detail["outputs"]:
                            if isinstance(output, dict) and "payment_addr" in output:
                                receiver_addr = output["payment_addr"]["bech32"]
                                if sender_addresses:  # Only add if we found valid senders
                                    receiver_senders[receiver_addr].update(sender_addresses)

                # Add a small delay between batches to avoid overwhelming the API
                time.sleep(0.01)

            except Exception as e:
                logger.error(f"Error processing transaction batch: {e}")
                logger.error(f"Batch hashes: {batch_hashes}")
                continue

            print(sender_addresses)

        return receiver_senders

    def calculate_h_index_series(self, days: int) -> pd.DataFrame:
        """Calculate daily h-index values for specified number of days"""
        blocks = self.get_block_range(days)

        # Group blocks by date
        daily_data = defaultdict(list)
        daily_receiver_senders = defaultdict(lambda: defaultdict(set))

        for block in blocks:
            block_date = datetime.fromtimestamp(block["block_time"]).date()
            daily_data[block_date].append(block)

        # Process each day
        results = []
        total_days = len(daily_data)
        for i, (date, day_blocks) in enumerate(daily_data.items(), 1):
            logger.info(f"Processing day {i}/{total_days}: {date}")

            # Process all blocks for the day
            for block in day_blocks:
                block_receiver_senders = self.process_block_transactions(block)
                for receiver, senders in block_receiver_senders.items():
                    daily_receiver_senders[date][receiver].update(senders)

            # Calculate h-index for the day
            h_index = self.calculate_daily_h_index(daily_receiver_senders[date])

            results.append(
                {
                    "date": date,
                    "h_index": h_index,
                    "blocks_processed": len(day_blocks),
                    "unique_receivers": len(daily_receiver_senders[date]),
                }
            )

        # Convert to DataFrame and sort by date
        df = pd.DataFrame(results)
        df = df.sort_values("date")
        return df


def main():
    try:
        # Initialize calculator
        calculator = CardanoHIndex()

        # Get number of days from user
        days = int(input("Enter number of days to analyze: "))

        # Calculate h-index series
        logger.info(f"Calculating h-index for the last {days} days...")
        df = calculator.calculate_h_index_series(days)

        # Display results
        print("\nDaily H-Index Values:")
        print(df.to_string(index=False))

        # Basic statistics
        print("\nSummary Statistics:")
        print(f"Average H-Index: {df['h_index'].mean():.2f}")
        print(f"Maximum H-Index: {df['h_index'].max()}")
        print(f"Minimum H-Index: {df['h_index'].min()}")
        print(f"Average Daily Unique Receivers: {df['unique_receivers'].mean():.2f}")

        # Save to CSV
        filename = f"cardano_h_index_{datetime.now().strftime('%Y%m%d')}.csv"
        df.to_csv(filename, index=False)
        print(f"\nResults saved to {filename}")

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise


if __name__ == "__main__":
    main()
