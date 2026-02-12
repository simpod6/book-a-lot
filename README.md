# book-a-lot

This is a web-based reservation system built with Flask. It allows users to create and cancel reservations for a single parking lot.

## Features

- User registration and login
- Create reservations
- Cancel reservations
- Statistics page

## TODO

All done.

## Installation

1. Clone the repository:

    ```sh
    git clone https://github.com/simpod6/book-a-lot.git
    ```

2. Navigate to the project directory:

    ```sh
    cd book-a-lot
    ```

3. Create a virtual environment:

    ```sh
    python -m venv venv
    ```

4. Activate the virtual environment:
    - On Windows:

        ```sh
        venv\Scripts\activate
        ```

    - On macOS/Linux:

        ```sh
        source venv/bin/activate
        ```

5. Install the required packages:

    ```sh
    pip install -r requirements.txt
    ```

## Usage

1. Set the desired environment variables. Check [.env-sample](.env-sample)

2. Run the application:

    ```sh
    flask run
    ```

3. Open your web browser and go to `http://127.0.0.1:5000/`.

## Routes

- `/` - Home page
- `/login` - Login for existing users
- `/logout` - Logout the current user
- `/register` - Register a new user
- `/reserve` - Create a new reservation
- `/cancel_reservation` - Cancel an existing reservation

## License

This project is licensed under the [MIT License](LICENSE).
