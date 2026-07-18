import requests

# Replace the following variables with your actual API URL and parameters
policy_id = 'da8c30857834c6ae7203935b89278c532b3995245295456f993e1d24'
asset_name = '4c51'
base_url = 'https://api.koios.rest/api/v0/asset_summary'
select_query = '_asset_policy=da8c30857834c6ae7203935b89278c532b3995245295456f993e1d24&_asset_name=4c51'
max_rows = 1000

def get_data_with_pagination(offset=0, limit=max_rows):
    headers = {"Range": f"{offset}-{offset+limit-1}"}
    response = requests.get(f"{base_url}?{select_query}", headers=headers)

    if response.status_code == 200:
        data = response.json()
        if not data:
            return []  # No more data available

        return data + get_data_with_pagination(offset + limit, limit)

    # Handle errors if needed
    print(f"Error: {response.status_code} - {response.text}")
    return []

# Call the function to retrieve all data
all_data = get_data_with_pagination()

# Print the complete data
print(all_data)