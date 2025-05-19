FROM python:3.11

# get main app code
COPY main_app /remas

WORKDIR /remas

# install requirements and remove cache files
RUN pip install --no-cache-dir -r requirements.txt

# expose application port
EXPOSE 8000

# run app
CMD [ "sh", "run_app.sh" ]

