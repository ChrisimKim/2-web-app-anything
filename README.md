# Web Application Exercise

A little exercise to build a web application following an agile development process. See the [instructions](instructions.md) for more detail.

## Product vision statement

Our platform empowers job seekers to organize, track, and manage all their job applications by providing an intuitive and structural way to maximize their chances of success.  

## User stories

User stories can be found as issues in our team's [Issues page](https://github.com/software-students-spring2025/2-web-app-anything/issues?q=is%3Aissue%20) or in [this file](./user-stories.md). 

## Steps necessary to run the software

### Prerequesites

Ensure you have the following downloaded:
- Python 
- pip (Python package manager)
- venv (Virtual environment)

### Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/software-students-spring2025/2-web-app-anything
    cd job-tracker
   ```
   
2. Create a virtual environment:
    ```sh
    python -m venv .venv # try 'python3' instead of 'python' if your system requires it

    # On macOS/Linux
    source .venv/bin/activate

    # On Windows
    .venv\Scripts\activate.bat
    ```

3. Install needed dependencies:
   ```sh
   pip install -r requirements.txt
   ```

4. Create a .env file in the job-tracker folder and load the environment variables, which can be found in the team's discord server.


5. Run the web app:
   ```sh
   python app.py # try 'python3' instead of 'python' if your system requires it
   ```

6. Open the web app in the browser using the link http://127.0.0.1:5000/

7. Use developer tools to browse on a mobile view (preferably iPhone 14 Pro Max)

## Task boards

Our workflow was broken down into two sprints for this project. The task board for Sprint 1 can be found [here](https://github.com/orgs/software-students-spring2025/projects/40), and the task board for Sprint 2 can be found [here](https://github.com/orgs/software-students-spring2025/projects/44).

## Figma Design

We have created both low-fidelity and high-fidelity for the website design and it can be found [here](https://www.figma.com/design/E8Zts9lPw8aI4A8I0yFpZB/Proj2?node-id=0-1&t=FvQsGjv0FRIx74oT-1).