# book-a-lot

This is a web-based reservation system built with Flask. It allows users to create and cancel reservations for a single parking lot.

## Features

- User registration and login
- Create reservations
- Cancel reservations
- Flash messages for user feedback

## TODO

- localize calendar
- better feedback instead of alert on reservation with empty selections

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

1. Run the application:

    ```sh
    flask run
    ```

2. Open your web browser and go to `http://127.0.0.1:5000/`.

## Routes

- `/register` - Register a new user
- `/login` - Login for existing users
- `/logout` - Logout the current user
- `/` - Home page
- `/reserve` - Create a new reservation
- `/cancel_reservation` - Cancel an existing reservation

## Contributing

1. Fork the repository
2. Create a new branch (`git checkout -b feature-branch`)
3. Commit your changes ([git commit -am 'Add new feature'](http://_vscodecontentref_/0))
4. Push to the branch (`git push origin feature-branch`)
5. Create a new Pull Request

## License

This project is licensed under the MIT License.
