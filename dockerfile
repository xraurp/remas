FROM python:3.11

# get main app code
COPY main_app /remas

WORKDIR /remas

# install requirements
RUN pip install -r requirements.txt
RUN pip cache purge

# expose application port
EXPOSE 8000

# run app
CMD [ "sh", "run_app.sh" ]

