FROM rasa/rasa-sdk:2.6.0

COPY actions /app/actions

USER root
RUN pip install --no-cache-dir -r /app/actions/requirements-actions.txt

CMD ["start", "--actions", "actions", "--debug"]
