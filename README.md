# PropertyDetails
Retrieves property details from HouseCanary API

# Running Locally
First configure your environment with [HouseCanary API keys](https://api-docs.housecanary.com/#authentication):
```
export HOUSECANARY_API_KEY=<your_api_key>
export HOUSECANARY_API_SECRET-<your_api_secret>
```
If you want to test the service without API keys you can set the following to mock the response from the HouseCanary API:
```
export HOUSECANARY_MOCK_RESPONSE=True
```

Run the server locally via
```
python manage.py runserver
```
Once the server has started you can test the implementation via:
```
http://localhost:8000/property/details?address=<address>&zipcode=<zipcode>
```

# Running Tests
Run the test suite via:
```
python manage.py test
```
