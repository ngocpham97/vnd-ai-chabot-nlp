"""Custom actions"""
import os
from typing import Dict, Text, Any, List
import logging
from dateutil import parser
import sqlalchemy as sa
import re
import uuid
# from dotenv import load_dotenv

from rasa_sdk.interfaces import Action
from rasa_sdk.events import (
	SlotSet,
	EventType,
	ActionExecuted,
	SessionStarted,
	Restarted,
	FollowupAction,
	UserUtteranceReverted,
	AllSlotsReset,
)

from rasa_sdk import Tracker
from rasa_sdk.executor import CollectingDispatcher

from actions.parsing import (
	parse_duckling_time_as_interval,
	parse_duckling_time,
	get_entity_details,
	parse_duckling_currency,
)

# from actions.posgresql import PostgreSQL

from actions.custom_forms import CustomFormValidationAction

from actions.constant import ENVIRONMENT_CONFIG_FILE
from actions.constant import loan_information_table, loan_information_columns, loan_register_table, loan_register_columns
 
# load_dotenv(dotenv_path=ENVIRONMENT_CONFIG_FILE)


logger = logging.getLogger(__name__)

# host                	 = os.environ['host']
# port                	 = os.environ['port']
# username            	 = os.environ['username']
# password            	 = os.environ['password']
# database            	 = os.environ['database']

# host                     = "10.1.21.3"
# port                     = 5432
# username                 = "postgres"
# password                 = "postgres"
# database                 = "postgres"

# global conn 
# conn = PostgreSQL(host=host, port=port, username=username, 
# 					password=password, database=database
# 				)

NEXT_FORM_NAME = {
	"borrow_money": "borrow_money_form",
}

FORM_DESCRIPTION = {
	"borrow_money_form": "borrow money",
}


class ActionBorrowMoney(Action):
	"""Transfers Money."""

	def name(self) -> Text:
		"""Unique identifier of the action"""
		return "action_borrow_money"

	async def run(
		self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
	) -> List[EventType]:
		"""Executes the action"""
		#get user information
		id = str(uuid.uuid4())
		user_name = tracker.get_slot('user_name')
		amount_of_money = float(tracker.get_slot('amount-of-money'))
		id_card = tracker.get_slot('id_card')
		telephone_number = tracker.get_slot('telephone_number')
		# insert user infomation to db
		# if user_name != None and amount_of_money != None and id_card != None and id_card != telephone_number:
		# 	conn.insert(table_name=loan_register_table, columns=loan_register_columns, values=[id, user_name, id_card, telephone_number, amount_of_money])

		slots = {
			"AA_CONTINUE_FORM": None,
			"zz_confirm_form": None,
			"user_name": None,
			"telephone_number": None,
			"id_card": None,
			# "email":None,
			# "location":None,
			# "age":None,
			# "job_title":None,
			# "income": None,
			"amount-of-money": None,
			"number": None,
		}

		if tracker.get_slot("zz_confirm_form") == "yes":
			user_name = tracker.get_slot("user_name")
			# email = tracker.get_slot("email")
			# location = tracker.get_slot("location")
			# job_title = tracker.get_slot("job_title")
			# income = tracker.get_slot("income")
			# age = tracker.get_slot("age")
			telephone_number = tracker.get_slot("telephone_number")
			id_card = tracker.get_slot("id_card")
			amount_of_money = float(tracker.get_slot("amount-of-money"))
			dispatcher.utter_message(response="utter_wait_complete")

		else:
			dispatcher.utter_message(response="utter_borrow_money_cancelled")

		return [SlotSet(slot, value) for slot, value in slots.items()]


class ValidateBorrowMoneyForm(CustomFormValidationAction):
	"""Validates Slots of the borrow_money_form"""

	def name(self) -> Text:
		"""Unique identifier of the action"""
		return "validate_borrow_money_form"

	def is_int(self, string: Text) -> bool:
		"""Check if a string is an integer."""

		try:
			int(string)
			return True
		except ValueError:
			return False

	async def validate_user_name(
		self,
		value: Text,
		dispatcher: CollectingDispatcher,
		tracker: Tracker,
		domain: Dict[Text, Any],
	) -> Dict[Text, Any]:
		"""Validates value of 'user_name' slot"""
		# It is possible that both Spacy & DIET extracted the user_name
		# Just pick the first one
		if isinstance(value, list):
			value = value[0]

		name = value.lower() if value else None
		if name is not None:
			return {"user_name": name.title()}

		dispatcher.utter_message(response="utter_unknown_name")
		return {"user_name": None}

	# async def validate_job_title(
	# 	self,
	# 	value: Text,
	# 	dispatcher: CollectingDispatcher,
	# 	tracker: Tracker,
	# 	domain: Dict[Text, Any],
	# ) -> Dict[Text, Any]:
	# 	"""Validates value of 'PERSON' slot"""
	# 	# It is possible that both Spacy & DIET extracted the PERSON
	# 	# Just pick the first one
	# 	if isinstance(value, list):
	# 		value = value[0]

	# 	name = value.lower() if value else None
	# 	if name is not None:
	# 		return {"job_title": name.title()}

	# 	dispatcher.utter_message(response="utter_unknown_name")
	# 	return {"job_title": None}

	async def validate_amount_of_money(
		self,
		value: Text,
		dispatcher: CollectingDispatcher,
		tracker: Tracker,
		domain: Dict[Text, Any],
	) -> Dict[Text, Any]:
		"""Validates value of 'amount_of_money' slot"""
		try:
			entity = get_entity_details(tracker, "amount-of-money")
			if not entity:
				entity = get_entity_details(tracker, "number")
			amount_currency = parse_duckling_currency(entity)
			if not amount_currency:
				raise TypeError
			if float(amount_currency.get("amount-of-money")) < 1000000 or float(amount_currency.get("amount-of-money")) > 5000000:
				dispatcher.utter_message(response="utter_insufficient_funds")
				return {"amount-of-money": None}
			return amount_currency
		except:
			pass

	async def validate_id_card(
		self,
		value: Text,
		dispatcher: CollectingDispatcher,
		tracker: Tracker,
		domain: Dict[Text, Any],
	) -> Dict[Text, Any]:
		"""Validates value of 'vendor_name' slot"""
		value = str(value)
		print("$$$$$$$$$$$$$$$$$$$$", value)
		if value and not any(map(str.isalpha, value)) and '[' not in value:
			return {"id_card": value}
		else:
			dispatcher.utter_message(response="utter_no_id_card")
			return {"id_card": None}

	async def validate_telephone_number(
		self,
		value: Text,
		dispatcher: CollectingDispatcher,
		tracker: Tracker,
		domain: Dict[Text, Any],
	) -> Dict[Text, Any]:
		"""Validates value of 'telephone_number' slot"""
		value = str(value)
		if value and not any(map(str.isalpha, value)) and '[' not in value:
			return {"telephone_number": value}
		else:
			dispatcher.utter_message(response="utter_no_telephone_number")
			return {"telephone_number": None}

	# async def validate_income(
	# 	self,
	# 	value: Text,
	# 	dispatcher: CollectingDispatcher,
	# 	tracker: Tracker,
	# 	domain: Dict[Text, Any],
	# ) -> Dict[Text, Any]:
	# 	"""Validates value of 'telephone_number' slot"""
	# 	value = str(value)
	# 	if value and not any(map(str.isalpha, value)) and '[' not in value:
	# 		return {"income": value}
	# 	else:
	# 		dispatcher.utter_message(response="utter_no_income")
	# 		return {"income": None}

	# async def validate_email(
	# 	self,
	# 	value: Text,
	# 	dispatcher: CollectingDispatcher,
	# 	tracker: Tracker,
	# 	domain: Dict[Text, Any],
	# ) -> Dict[Text, Any]:
	# 	"""Validates value of 'email' slot"""
	# 	value = str(value)
	# 	if re.match("^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$", value):
	# 		return {"email": value}
	# 	else:
	# 		dispatcher.utter_message(response="utter_no_email")
	# 		# validation failed, set this slot to None, meaning the
	# 		# user will be asked for the slot again
	# 		return {"email": None}

	# async def validate_location(
	# 	self,
	# 	value: Text,
	# 	dispatcher: CollectingDispatcher,
	# 	tracker: Tracker,
	# 	domain: Dict[Text, Any],
	# ) -> Dict[Text, Any]:
	# 	"""Validates value of 'location' slot"""
	# 	value = str(value)
	# 	if 2 < len(value) < 50:
	# 		# validation succeeded, set the value of the "name" slot to value
	# 		return {"location": value}
	# 	else:
	# 		dispatcher.utter_message(response="utter_location_null")
	# 		# validation failed, set this slot to None, meaning the
	# 		# user will be asked for the slot again
	# 		return {"location": None}

	# async def validate_age(
	# 	self,
	# 	value: Text,
	# 	dispatcher: CollectingDispatcher,
	# 	tracker: Tracker,
	# 	domain: Dict[Text, Any],
	# ) -> Dict[Text, Any]:
	# 	"""Validates value of 'age' slot"""
	# 	if self.is_int(value) and int(value) >= 19 and int(value) <= 100:
	# 		return {'age': value}
	# 	else:
	# 		dispatcher.utter_message(response='utter_wrong_age')
	# 		return {'age': None}

	async def validate_zz_confirm_form(
		self,
		value: Text,
		dispatcher: CollectingDispatcher,
		tracker: Tracker,
		domain: Dict[Text, Any],
	) -> Dict[Text, Any]:
		"""Validates value of 'zz_confirm_form' slot"""
		if value in ["yes", "no"]:
			return {"zz_confirm_form": value}

		return {"zz_confirm_form": None}


class ActionChangeOrder(Action):
	def name(self) -> Text:
		return 'action_change_inform'

	async def run(
		self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
	) -> List[EventType]:
		
		if tracker.latest_message['intent'].get('name') == "change_person":
			return [SlotSet("user_name", None)]
		elif tracker.latest_message['intent'].get('name') == "change_email":
			return [SlotSet("email", None)]
		elif tracker.latest_message['intent'].get('name') == "change_location":
			return [SlotSet("location", None)]
		elif tracker.latest_message['intent'].get('name') == "change_age":
			return [SlotSet("age", None)]
		elif tracker.latest_message['intent'].get('name') == "change_telephone_number":
			return [SlotSet("telephone_number", None)]
		elif tracker.latest_message['intent'].get('name') == "change_id_card":
			return [SlotSet("id_card", None)]
		elif tracker.latest_message['intent'].get('name') == "change_amount_of_money":
			return [SlotSet("amount-of-money", None)]
		elif tracker.latest_message['intent'].get('name') == "change_income":
			return [SlotSet("income", None)]
		elif tracker.latest_message['intent'].get('name') == "change_job_title":
			return [SlotSet("job_title", None)]
		elif tracker.latest_message['intent'].get('name') == "change_house_type":
			return [SlotSet("house_type", None)]
		else:
			dispatcher.utter_message(response="utter_handoff")

		return []


class ActionShowPayBackTime(Action):
	"""Lists the contents of then known_recipients slot"""

	def name(self) -> Text:
		"""Unique identifier of the action"""
		return "action_show_payback_time"

	async def run(
		self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
	) -> List[EventType]:
		"""Executes the custom action"""
		dispatcher.utter_message(
			response="utter_payback_time",
		)

		events = []
		active_form_name = tracker.active_form.get("name")
		if active_form_name:
			dispatcher.utter_message(
				response="utter_ask_continue",
			)
			# keep the tracker clean for the predictions with form switch stories
			events.append(UserUtteranceReverted())
			# trigger utter_ask_{form}_AA_CONTINUE_FORM, by making it the requested_slot
			events.append(SlotSet("AA_CONTINUE_FORM", None))
			# # avoid that bot goes in listen mode after UserUtteranceReverted
			events.append(FollowupAction(active_form_name))

		return events


class ActionShowInterestRate(Action):
	"""Lists the transfer charges"""

	def name(self) -> Text:
		"""Unique identifier of the action"""
		return "action_show_interest_rate"

	async def run(
		self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
	) -> List[EventType]:
		"""Executes the custom action"""
		dispatcher.utter_message(response="utter_interest_rate")

		events = []
		active_form_name = tracker.active_form.get("name")
		if active_form_name:
			dispatcher.utter_message(
				response="utter_ask_continue",
			)
			# keep the tracker clean for the predictions with form switch stories
			events.append(UserUtteranceReverted())
			# trigger utter_ask_{form}_AA_CONTINUE_FORM, by making it the requested_slot
			events.append(SlotSet("AA_CONTINUE_FORM", None))
			# # avoid that bot goes in listen mode after UserUtteranceReverted
			events.append(FollowupAction(active_form_name))

		return events

class ActionInformationCompany(Action):
	"""Lists the transfer charges"""

	def name(self) -> Text:
		"""Unique identifier of the action"""
		return "action_information_company"

	async def run(
		self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
	) -> List[EventType]:
		"""Executes the custom action"""
		dispatcher.utter_message(response="utter_information_company")

		events = []
		active_form_name = tracker.active_form.get("name")
		if active_form_name:
			dispatcher.utter_message(
				response="utter_ask_continue",
			)
			# keep the tracker clean for the predictions with form switch stories
			events.append(UserUtteranceReverted())
			# trigger utter_ask_{form}_AA_CONTINUE_FORM, by making it the requested_slot
			events.append(SlotSet("AA_CONTINUE_FORM", None))
			# # avoid that bot goes in listen mode after UserUtteranceReverted
			events.append(FollowupAction(active_form_name))

		return events

class ActionShowPaymentMethods(Action):
	"""Lists the transfer charges"""

	def name(self) -> Text:
		"""Unique identifier of the action"""
		return "action_payment_methods"

	async def run(
		self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
	) -> List[EventType]:
		"""Executes the custom action"""
		dispatcher.utter_message(response="utter_payment_methods")

		events = []
		active_form_name = tracker.active_form.get("name")
		if active_form_name:
			dispatcher.utter_message(
				response="utter_ask_continue",
			)
			# keep the tracker clean for the predictions with form switch stories
			events.append(UserUtteranceReverted())
			# trigger utter_ask_{form}_AA_CONTINUE_FORM, by making it the requested_slot
			events.append(SlotSet("AA_CONTINUE_FORM", None))
			# # avoid that bot goes in listen mode after UserUtteranceReverted
			events.append(FollowupAction(active_form_name))

		return events


class ActionShowInformationCompany(Action):
	"""Lists the transfer charges"""

	def name(self) -> Text:
		"""Unique identifier of the action"""
		return "action_late_payment"

	async def run(
		self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
	) -> List[EventType]:
		"""Executes the custom action"""
		dispatcher.utter_message(response="utter_late_payment")

		events = []
		active_form_name = tracker.active_form.get("name")
		if active_form_name:
			# keep the tracker clean for the predictions with form switch stories
			events.append(UserUtteranceReverted())
			# trigger utter_ask_{form}_AA_CONTINUE_FORM, by making it the requested_slot
			events.append(SlotSet("AA_CONTINUE_FORM", None))
			# # avoid that bot goes in listen mode after UserUtteranceReverted
			events.append(FollowupAction(active_form_name))

		return events


class ActionSessionStart(Action):
	"""Executes at start of session"""

	def name(self) -> Text:
		"""Unique identifier of the action"""
		return "action_session_start"

	@staticmethod
	def _slot_set_events_from_tracker(
		tracker: "Tracker",
	) -> List["SlotSet"]:
		"""Fetches SlotSet events from tracker and carries over keys and values"""

		# when restarting most slots should be reset
		relevant_slots = ["currency"]

		return [
			SlotSet(
				key=event.get("name"),
				value=event.get("value"),
			)
			for event in tracker.events
			if event.get("event") == "slot" and event.get("name") in relevant_slots
		]

	async def run(
		self,
		dispatcher: CollectingDispatcher,
		tracker: Tracker,
		domain: Dict[Text, Any],
	) -> List[EventType]:
		"""Executes the custom action"""
		# the session should begin with a `session_started` event
		events = [SessionStarted()]

		events.extend(self._slot_set_events_from_tracker(tracker))
		currency = 'VND'
		# initialize slots from mock profile
		events.append(SlotSet("currency", currency))

		# add `action_listen` at the end
		events.append(ActionExecuted("action_listen"))

		return events


class ActionRestart(Action):
	"""Executes after restart of a session"""

	def name(self) -> Text:
		"""Unique identifier of the action"""
		return "action_restart"

	async def run(
		self,
		dispatcher: CollectingDispatcher,
		tracker: Tracker,
		domain: Dict[Text, Any],
	) -> List[EventType]:
		"""Executes the custom action"""
		return [Restarted(), FollowupAction("action_session_start")]


class ActionSwitchFormsAsk(Action):
	"""Asks to switch forms"""

	def name(self) -> Text:
		return "action_switch_forms_ask"

	async def run(
		self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
	) -> List[EventType]:
		"""Executes the custom action"""
		active_form_name = tracker.active_form.get("name")
		intent_name = tracker.latest_message["intent"]["name"]
		next_form_name = NEXT_FORM_NAME.get(intent_name)

		if (
			active_form_name not in FORM_DESCRIPTION.keys()
			or next_form_name not in FORM_DESCRIPTION.keys()
		):
			logger.debug(
				f"Cannot create text for `active_form_name={active_form_name}` & "
				f"`next_form_name={next_form_name}`"
			)
			next_form_name = None
		else:
			text = (
				f"We haven't completed the {FORM_DESCRIPTION[active_form_name]} yet. "
				f"Are you sure you want to switch to {FORM_DESCRIPTION[next_form_name]}?"
			)
			buttons = [
				{"payload": "/affirm", "title": "Yes"},
				{"payload": "/deny", "title": "No"},
			]
			dispatcher.utter_message(text=text, buttons=buttons)
		return [SlotSet("next_form_name", next_form_name)]


class ActionSwitchFormsDeny(Action):
	"""Does not switch forms"""

	def name(self) -> Text:
		return "action_switch_forms_deny"

	async def run(
		self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
	) -> List[EventType]:
		"""Executes the custom action"""
		active_form_name = tracker.active_form.get("name")

		if active_form_name not in FORM_DESCRIPTION.keys():
			logger.debug(
				f"Cannot create text for `active_form_name={active_form_name}`."
			)
		else:
			text = f"Ok, let's continue with the {FORM_DESCRIPTION[active_form_name]}."
			dispatcher.utter_message(text=text)

		return [SlotSet("next_form_name", None)]


class ActionSwitchFormsAffirm(Action):
	"""Switches forms"""

	def name(self) -> Text:
		return "action_switch_forms_affirm"

	async def run(
		self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
	) -> List[EventType]:
		"""Executes the custom action"""
		active_form_name = tracker.active_form.get("name")
		next_form_name = tracker.get_slot("next_form_name")

		if (
			active_form_name not in FORM_DESCRIPTION.keys()
			or next_form_name not in FORM_DESCRIPTION.keys()
		):
			logger.debug(
				f"Cannot create text for `active_form_name={active_form_name}` & "
				f"`next_form_name={next_form_name}`"
			)
		else:
			text = (
				f"Chúng ta sẽ chuyển từ  {FORM_DESCRIPTION[active_form_name]} "
				f"đến {FORM_DESCRIPTION[next_form_name]}. "
				f"Một khi hoàn tất bạn có thể quay trở lại để hoàn tất những thông tin."
			)
			dispatcher.utter_message(text=text)

		return [
			SlotSet("previous_form_name", active_form_name),
			SlotSet("next_form_name", None),
		]


class ActionSwitchBackAsk(Action):
	"""Asks to switch back to previous form"""

	def name(self) -> Text:
		return "action_switch_back_ask"

	async def run(
		self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
	) -> List[EventType]:
		"""Executes the custom action"""
		previous_form_name = tracker.get_slot("previous_form_name")

		if previous_form_name not in FORM_DESCRIPTION.keys():
			logger.debug(
				f"Cannot create text for `previous_form_name={previous_form_name}`"
			)
			previous_form_name = None
		else:
			text = (
				f"Bạn có muốn hoàn tất thông tin "
				f"{FORM_DESCRIPTION[previous_form_name]} bây giờ?."
			)
			buttons = [
				{"payload": "/affirm", "title": "Yes"},
				{"payload": "/deny", "title": "No"},
			]
			dispatcher.utter_message(text=text, buttons=buttons)

		return [SlotSet("previous_form_name", None)]


class ActionResetAllSlots(Action):

	def name(self):
		return "action_reset_all_slots"

	def run(self, dispatcher, tracker, domain):
		gender_value = tracker.get_slot("gender_value")
		slots = {
            "AA_CONTINUE_FORM": None,
            "PERSON": None,
            "user_name": None,
            "age": None,
            "amount-of-money": None,
            "company": None,
            "currency": "VND",
            "email": None,
            "end_time": None,
            "end_time_formatted": None,
            "grain": None,
            "handoff_to": None,
            "id_card": None,
            "income": None,
            "job_title": None,
            "location": None,
            "next_form_name": None,
            "number": None,
            "previous_form_name": None,
            "repeated_validation_failures": None,
            "requested_slot": None,
            "start_time": None,
            "start_time_formatted": None,
            "telephone_number": None,
            "time": None,
            "time_formatted": None,
            "zz_confirm_form": None,
            "loan_name": None,
            "gender_value": gender_value,
		}

		return [SlotSet(slot, value) for slot, value in slots.items()]


class ActionNLUFallBack(Action):
	"""Lists the contents of then known_recipients slot"""

	def name(self) -> Text:
		"""Unique identifier of the action"""
		return "action_default"

	async def run(
		self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
	) -> List[EventType]:
		"""Executes the custom action"""
		dispatcher.utter_message(
		   response="utter_default",
		)

		events = []
		active_form_name = tracker.active_form.get("name")
		if active_form_name:
			# keep the tracker clean for the predictions with form switch stories
			events.append(UserUtteranceReverted())
			# trigger utter_ask_{form}_AA_CONTINUE_FORM, by making it the requested_slot
			events.append(SlotSet("AA_CONTINUE_FORM", None))
			# # avoid that bot goes in listen mode after UserUtteranceReverted
			events.append(FollowupAction(active_form_name))

		return events


class ActionOutOfScope(Action):
	"""Lists the contents of then known_recipients slot"""

	def name(self) -> Text:
		"""Unique identifier of the action"""
		return "action_out_of_scope"

	async def run(
		self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
	) -> List[EventType]:
		"""Executes the custom action"""
		dispatcher.utter_message(
		   response="utter_out_of_scope",
		)
		dispatcher.utter_message(
		   response="utter_bot_function",
		)


		events = []
		active_form_name = tracker.active_form.get("name")
		if active_form_name:
			# keep the tracker clean for the predictions with form switch stories
			dispatcher.utter_message(
				response="utter_ask_continue",
			)
			events.append(UserUtteranceReverted())
			# trigger utter_ask_{form}_AA_CONTINUE_FORM, by making it the requested_slot
			events.append(SlotSet("AA_CONTINUE_FORM", None))
			# # avoid that bot goes in listen mode after UserUtteranceReverted
			events.append(FollowupAction(active_form_name))

		return events


class ActionShowAllLoan(Action):
    """Lists the contents of then known_recipients slot"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "action_show_all_loan"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        """Executes the custom action"""
        # loans = conn.list_loans()
        # formatted_loans = "\n" + "\n".join(
        #     [f"- {loan[0]} : {loan[1]}VND" for loan in loans]
        # )
        formatted_loans= ""
        dispatcher.utter_message(
            response="utter_loan_information",
            formatted_loans=formatted_loans,
        )
        dispatcher.utter_message(
            response="utter_loan_information_addtion",
        )

        events = []
        active_form_name = tracker.active_form.get("name")
        if active_form_name:
            dispatcher.utter_message(
				response="utter_ask_continue",
			)
            # keep the tracker clean for the predictions with form switch stories
            events.append(UserUtteranceReverted())
            # trigger utter_ask_{form}_AA_CONTINUE_FORM, by making it the requested_slot
            events.append(SlotSet("AA_CONTINUE_FORM", None))
            # # avoid that bot goes in listen mode after UserUtteranceReverted
            events.append(FollowupAction(active_form_name))

        return events


# class ActionShowDetailLoan(Action):
#     """Lists the contents of then known_recipients slot"""

#     def name(self) -> Text:
#         """Unique identifier of the action"""
#         return "action_show_detail_loan"

#     async def run(
#         self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
#     ) -> List[EventType]:
#         """Executes the custom action"""
#         loan_name = tracker.get_slot("loan_name")
#         formatted_loan = ""
#         # loan_detail = conn.detail_loan(['loan_name'], [loan_name])
#         # formatted_loan = "- Tên gói vay   		: {} \n- Số tiền       	        : {}VND \n- Hình thức vay 		: {} \n- Yêu cầu       		: {} \
#         # \n- Thời hạn vay  		: {} \n- Lãi xuất     		        : {} \n- Thời gian giải ngân           : {}".format(loan_detail[0][0], loan_detail[0][1], loan_detail[0][2], loan_detail[0][3], loan_detail[0][4], loan_detail[0][5], loan_detail[0][6])
#         dispatcher.utter_message(
#             response="utter_detail_loan",
#             formatted_loan=formatted_loan,
#         )

#         events = []
#         active_form_name = tracker.active_form.get("name")
#         if active_form_name:
#             # keep the tracker clean for the predictions with form switch stories
#             events.append(UserUtteranceReverted())
#             # trigger utter_ask_{form}_AA_CONTINUE_FORM, by making it the requested_slot
#             events.append(SlotSet("AA_CONTINUE_FORM", None))
#             # # avoid that bot goes in listen mode after UserUtteranceReverted
#             events.append(FollowupAction(active_form_name))

#         return events


class ActionConfirmCallBackTime(Action):
	"""Lists the contents of then known_recipients slot"""

	def name(self) -> Text:
		"""Unique identifier of the action"""
		return "action_confirm_callback_time"

	async def run(
		self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
	) -> List[EventType]:
		"""Executes the custom action"""
		time = tracker.get_slot('time')
		time = time.split('T')
		hour = time[1][:5]
		day  = time[0][8:]
		month = time[0][5:7]
		year  = time[0][0:4]
		formatted_time = "{} ngày {} tháng {} năm {}".format(hour, day, month, year)
		dispatcher.utter_message(
		   response="utter_confirm_callback_time",
		   formatted_time=formatted_time,
		)

		events = []
		active_form_name = tracker.active_form.get("name")
		if active_form_name:
			# keep the tracker clean for the predictions with form switch stories
			events.append(UserUtteranceReverted())
			# trigger utter_ask_{form}_AA_CONTINUE_FORM, by making it the requested_slot
			events.append(SlotSet("AA_CONTINUE_FORM", None))
			# # avoid that bot goes in listen mode after UserUtteranceReverted
			events.append(FollowupAction(active_form_name))

		return events


class ActionRepeat(Action):
	"""Lists the contents of then known_recipients slot"""

	def name(self) -> Text:
		"""Unique identifier of the action"""
		return "action_repeat"

	async def run(
		self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
	) -> List[EventType]:
		"""Executes the custom action"""
		events = []
		active_form_name = tracker.active_form.get("name")
		if not active_form_name:
			bot_events = next(e for e in reversed(tracker.events) if e["event"]== "bot")
			dispatcher.utter_message(bot_events.get("text"))
		if active_form_name:
			# keep the tracker clean for the predictions with form switch stories
			events.append(UserUtteranceReverted())
			# trigger utter_ask_{form}_AA_CONTINUE_FORM, by making it the requested_slot
			events.append(SlotSet("AA_CONTINUE_FORM", None))
			# # avoid that bot goes in listen mode after UserUtteranceReverted
			events.append(FollowupAction(active_form_name))

		return events


class ActionTimeGetMoney(Action):
	"""Lists the contents of then known_recipients slot"""

	def name(self) -> Text:
		"""Unique identifier of the action"""
		return "action_time_get_money"

	async def run(
		self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
	) -> List[EventType]:
		"""Executes the custom action"""
		dispatcher.utter_message(
		   response="utter_time_get_money",
		)
		events = []
		active_form_name = tracker.active_form.get("name")
		if active_form_name:
			dispatcher.utter_message(
				response="utter_ask_continue",
			)
			# keep the tracker clean for the predictions with form switch stories
			events.append(UserUtteranceReverted())
			# trigger utter_ask_{form}_AA_CONTINUE_FORM, by making it the requested_slot
			events.append(SlotSet("AA_CONTINUE_FORM", None))
			# # avoid that bot goes in listen mode after UserUtteranceReverted
			events.append(FollowupAction(active_form_name))

		return events

class ActionMethobGetMoney(Action):
	"""Lists the contents of then known_recipients slot"""

	def name(self) -> Text:
		"""Unique identifier of the action"""
		return "action_methob_get_money"

	async def run(
		self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
	) -> List[EventType]:
		"""Executes the custom action"""
		dispatcher.utter_message(
		   response="utter_methob_get_money",
		)
		events = []
		active_form_name = tracker.active_form.get("name")
		if active_form_name:
			dispatcher.utter_message(
				response="utter_ask_continue",
			)
			# keep the tracker clean for the predictions with form switch stories
			events.append(UserUtteranceReverted())
			# trigger utter_ask_{form}_AA_CONTINUE_FORM, by making it the requested_slot
			events.append(SlotSet("AA_CONTINUE_FORM", None))
			# # avoid that bot goes in listen mode after UserUtteranceReverted
			events.append(FollowupAction(active_form_name))

		return events

class ActionPurposeInformation(Action):
	"""Lists the contents of then known_recipients slot"""

	def name(self) -> Text:
		"""Unique identifier of the action"""
		return "action_purpose_information"

	async def run(
		self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
	) -> List[EventType]:
		"""Executes the custom action"""
		dispatcher.utter_message(
		   response="utter_purpose_information",
		)
		events = []
		active_form_name = tracker.active_form.get("name")
		if active_form_name:
			# keep the tracker clean for the predictions with form switch stories
			events.append(UserUtteranceReverted())
			# trigger utter_ask_{form}_AA_CONTINUE_FORM, by making it the requested_slot
			events.append(SlotSet("AA_CONTINUE_FORM", None))
			# # avoid that bot goes in listen mode after UserUtteranceReverted
			events.append(FollowupAction(active_form_name))

		return events

class ActionAcceptOrNot(Action):
	"""Lists the contents of then known_recipients slot"""

	def name(self) -> Text:
		"""Unique identifier of the action"""
		return "action_accept_or_not"

	async def run(
		self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
	) -> List[EventType]:
		"""Executes the custom action"""
		dispatcher.utter_message(
		   response="utter_accept_or_not",
		)
		events = []
		active_form_name = tracker.active_form.get("name")
		if active_form_name:
			# keep the tracker clean for the predictions with form switch stories
			events.append(UserUtteranceReverted())
			# trigger utter_ask_{form}_AA_CONTINUE_FORM, by making it the requested_slot
			events.append(SlotSet("AA_CONTINUE_FORM", None))
			# # avoid that bot goes in listen mode after UserUtteranceReverted
			events.append(FollowupAction(active_form_name))



# class ActionSetGender(Action):
	
# 	def name(self) -> Text:
# 		"""Unique identifier of the action"""
# 		return "action_set_gender"

# 	async def run(
# 		self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
# 	) -> List[EventType]:
# 		gender_value = list(tracker.get_latest_entity_values('gender_value'))[0]
# 		slots = {
# 			"gender_value": gender_value,
#         }
# 		return [SlotSet(slot, value) for slot, value in slots.items()]



class ActionCostConsulting(Action):
    """Lists the contents of then known_recipients slot"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "action_cost_consulting"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        """Executes the custom action"""
        formatted_number_money = tracker.get_slot("number")
        formatted_profit = int(0.08 * formatted_number_money)
        formatted_money_received = int(formatted_number_money - formatted_profit)
        dispatcher.utter_message(
            response="utter_cost_consulting",
        	formatted_number_money=formatted_number_money,
			formatted_profit=formatted_profit,
			formatted_money_received=formatted_money_received,
        )

        events = []
        active_form_name = tracker.active_form.get("name")
        if active_form_name:
            # keep the tracker clean for the predictions with form switch stories
            events.append(UserUtteranceReverted())
            # trigger utter_ask_{form}_AA_CONTINUE_FORM, by making it the requested_slot
            events.append(SlotSet("AA_CONTINUE_FORM", None))
            # # avoid that bot goes in listen mode after UserUtteranceReverted
            events.append(FollowupAction(active_form_name))

        return events

class ActionOverdueInterest(Action):
    """Lists the contents of then known_recipients slot"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "action_overdue_interest"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        """Executes the custom action"""
        dispatcher.utter_message(
            response="utter_overdue_interest",
        )
        formatted_number_money = tracker.get_slot("number")
        if formatted_number_money > 5000000:
            formatted_number_money = 5000000
        if formatted_number_money != None and formatted_number_money>= 1000000:
            formatted_profit = int(0.3/365 * 5 * formatted_number_money)
            formatted_penalties = int(0.08 * formatted_number_money)
            formatted_compensation = 9000 * 5
            formatted_total = formatted_profit + formatted_penalties + formatted_compensation

            dispatcher.utter_message(
				response="utter_detail_overdue_interest",
				formatted_number_money=formatted_number_money,
				formatted_profit=formatted_profit,
				formatted_penalties=formatted_penalties,
				formatted_compensation=formatted_compensation,
				formatted_total=formatted_total,
			)
        events = []
        active_form_name = tracker.active_form.get("name")
        if active_form_name:
            # keep the tracker clean for the predictions with form switch stories
            events.append(UserUtteranceReverted())
            # trigger utter_ask_{form}_AA_CONTINUE_FORM, by making it the requested_slot
            events.append(SlotSet("AA_CONTINUE_FORM", None))
            # # avoid that bot goes in listen mode after UserUtteranceReverted
            events.append(FollowupAction(active_form_name))

        return events

class ActionThankYou(Action):
    """Lists the contents of then known_recipients slot"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "action_thank_you"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        """Executes the custom action"""
        dispatcher.utter_message(
            response="utter_noworries",
        )
		
        events = []
        active_form_name = tracker.active_form.get("name")
        if active_form_name: 
            dispatcher.utter_message(
				response="utter_ask_continue",
			)
            # keep the tracker clean for the predictions with form switch stories
            events.append(UserUtteranceReverted())
            # trigger utter_ask_{form}_AA_CONTINUE_FORM, by making it the requested_slot
            events.append(SlotSet("AA_CONTINUE_FORM", None))
            # # avoid that bot goes in listen mode after UserUtteranceReverted
            events.append(FollowupAction(active_form_name))

        return events

class ActionLoanHelper(Action):
    """Lists the contents of then known_recipients slot"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "action_loan_helper"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        """Executes the custom action"""
        dispatcher.utter_message(
            response="utter_loan_helper",
        )
		
        events = []
        active_form_name = tracker.active_form.get("name")
        if active_form_name: 
            dispatcher.utter_message(
				response="utter_ask_continue",
			)
            # keep the tracker clean for the predictions with form switch stories
            events.append(UserUtteranceReverted())
            # trigger utter_ask_{form}_AA_CONTINUE_FORM, by making it the requested_slot
            events.append(SlotSet("AA_CONTINUE_FORM", None))
            # # avoid that bot goes in listen mode after UserUtteranceReverted
            events.append(FollowupAction(active_form_name))

        return events
	
class ActionInformationProvided(Action):
    """Lists the contents of then known_recipients slot"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "action_information_provided"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        """Executes the custom action"""
        dispatcher.utter_message(
            response="utter_information_provided",
        )
		
        events = []
        active_form_name = tracker.active_form.get("name")
        if active_form_name: 
            dispatcher.utter_message(
				response="utter_ask_continue",
			)
            # keep the tracker clean for the predictions with form switch stories
            events.append(UserUtteranceReverted())
            # trigger utter_ask_{form}_AA_CONTINUE_FORM, by making it the requested_slot
            events.append(SlotSet("AA_CONTINUE_FORM", None))
            # # avoid that bot goes in listen mode after UserUtteranceReverted
            events.append(FollowupAction(active_form_name))

        return events

class ActionSignContract(Action):
    """Lists the contents of then known_recipients slot"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "action_sign_contract"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        """Executes the custom action"""
        dispatcher.utter_message(
            response="utter_sign_contract",
        )
		
        events = []
        active_form_name = tracker.active_form.get("name")
        if active_form_name: 
            dispatcher.utter_message(
				response="utter_ask_continue",
			)
            # keep the tracker clean for the predictions with form switch stories
            events.append(UserUtteranceReverted())
            # trigger utter_ask_{form}_AA_CONTINUE_FORM, by making it the requested_slot
            events.append(SlotSet("AA_CONTINUE_FORM", None))
            # # avoid that bot goes in listen mode after UserUtteranceReverted
            events.append(FollowupAction(active_form_name))

        return events
	
class ActionSignContract(Action):
    """Lists the contents of then known_recipients slot"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "action_sign_contract"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        """Executes the custom action"""
        dispatcher.utter_message(
            response="utter_sign_contract",
        )
		
        events = []
        active_form_name = tracker.active_form.get("name")
        if active_form_name: 
            dispatcher.utter_message(
				response="utter_ask_continue",
			)
            # keep the tracker clean for the predictions with form switch stories
            events.append(UserUtteranceReverted())
            # trigger utter_ask_{form}_AA_CONTINUE_FORM, by making it the requested_slot
            events.append(SlotSet("AA_CONTINUE_FORM", None))
            # # avoid that bot goes in listen mode after UserUtteranceReverted
            events.append(FollowupAction(active_form_name))

        return events

class ActionLoanExtention(Action):
    """Lists the contents of then known_recipients slot"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "action_loan_extension"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        """Executes the custom action"""
        dispatcher.utter_message(
            response="utter_loan_extension",
        )
		
        events = []
        active_form_name = tracker.active_form.get("name")
        if active_form_name: 
            dispatcher.utter_message(
				response="utter_ask_continue",
			)
            # keep the tracker clean for the predictions with form switch stories
            events.append(UserUtteranceReverted())
            # trigger utter_ask_{form}_AA_CONTINUE_FORM, by making it the requested_slot
            events.append(SlotSet("AA_CONTINUE_FORM", None))
            # # avoid that bot goes in listen mode after UserUtteranceReverted
            events.append(FollowupAction(active_form_name))

        return events

	
class ActionLendingArea(Action):
    """Lists the contents of then known_recipients slot"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "action_lending_area"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        """Executes the custom action"""
        dispatcher.utter_message(
            response="utter_lending_area",
        )
		
        events = []
        active_form_name = tracker.active_form.get("name")
        if active_form_name: 
            dispatcher.utter_message(
				response="utter_ask_continue",
			)
            # keep the tracker clean for the predictions with form switch stories
            events.append(UserUtteranceReverted())
            # trigger utter_ask_{form}_AA_CONTINUE_FORM, by making it the requested_slot
            events.append(SlotSet("AA_CONTINUE_FORM", None))
            # # avoid that bot goes in listen mode after UserUtteranceReverted
            events.append(FollowupAction(active_form_name))

        return events

class ActionLoanConsulting(Action):
    """Lists the contents of then known_recipients slot"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "action_loan_consulting"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        """Executes the custom action"""
        dispatcher.utter_message(
            response="utter_loan_consulting",
        )
		
        events = []
        active_form_name = tracker.active_form.get("name")
        if active_form_name: 
            dispatcher.utter_message(
				response="utter_ask_continue",
			)
            # keep the tracker clean for the predictions with form switch stories
            events.append(UserUtteranceReverted())
            # trigger utter_ask_{form}_AA_CONTINUE_FORM, by making it the requested_slot
            events.append(SlotSet("AA_CONTINUE_FORM", None))
            # # avoid that bot goes in listen mode after UserUtteranceReverted
            events.append(FollowupAction(active_form_name))

        return events

class ActionExchangeFee(Action):
    """Lists the contents of then known_recipients slot"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "action_exchange_fee"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        """Executes the custom action"""
        dispatcher.utter_message(
            response="utter_exchange_fee",
        )
		
        events = []
        active_form_name = tracker.active_form.get("name")
        if active_form_name: 
            dispatcher.utter_message(
				response="utter_ask_continue",
			)
            # keep the tracker clean for the predictions with form switch stories
            events.append(UserUtteranceReverted())
            # trigger utter_ask_{form}_AA_CONTINUE_FORM, by making it the requested_slot
            events.append(SlotSet("AA_CONTINUE_FORM", None))
            # # avoid that bot goes in listen mode after UserUtteranceReverted
            events.append(FollowupAction(active_form_name))

        return events

class ActionHighInterest(Action):
    """Lists the contents of then known_recipients slot"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "action_high_interest"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        """Executes the custom action"""
        dispatcher.utter_message(
            response="utter_high_interest",
        )
		
        events = []
        active_form_name = tracker.active_form.get("name")
        if active_form_name: 
            dispatcher.utter_message(
				response="utter_ask_continue",
			)
            # keep the tracker clean for the predictions with form switch stories
            events.append(UserUtteranceReverted())
            # trigger utter_ask_{form}_AA_CONTINUE_FORM, by making it the requested_slot
            events.append(SlotSet("AA_CONTINUE_FORM", None))
            # # avoid that bot goes in listen mode after UserUtteranceReverted
            events.append(FollowupAction(active_form_name))

        return events

class ActionLoanType(Action):
    """Lists the contents of then known_recipients slot"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "action_loan_type"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        """Executes the custom action"""
        dispatcher.utter_message(
            response="utter_loan_type",
        )
		
        events = []
        active_form_name = tracker.active_form.get("name")
        if active_form_name: 
            dispatcher.utter_message(
				response="utter_ask_continue",
			)
            # keep the tracker clean for the predictions with form switch stories
            events.append(UserUtteranceReverted())
            # trigger utter_ask_{form}_AA_CONTINUE_FORM, by making it the requested_slot
            events.append(SlotSet("AA_CONTINUE_FORM", None))
            # # avoid that bot goes in listen mode after UserUtteranceReverted
            events.append(FollowupAction(active_form_name))

        return events

class ActionLoanProcess(Action):
    """Lists the contents of then known_recipients slot"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "action_loan_process"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        """Executes the custom action"""
        dispatcher.utter_message(
            response="utter_loan_process",
        )
		
        events = []
        active_form_name = tracker.active_form.get("name")
        if active_form_name: 
            dispatcher.utter_message(
				response="utter_ask_continue",
			)
            # keep the tracker clean for the predictions with form switch stories
            events.append(UserUtteranceReverted())
            # trigger utter_ask_{form}_AA_CONTINUE_FORM, by making it the requested_slot
            events.append(SlotSet("AA_CONTINUE_FORM", None))
            # # avoid that bot goes in listen mode after UserUtteranceReverted
            events.append(FollowupAction(active_form_name))

        return events

class ActionIncentives(Action):
    """Lists the contents of then known_recipients slot"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "action_incentives"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        """Executes the custom action"""
        dispatcher.utter_message(
            response="utter_incentives",
        )
		
        events = []
        active_form_name = tracker.active_form.get("name")
        if active_form_name: 
            dispatcher.utter_message(
				response="utter_ask_continue",
			)
            # keep the tracker clean for the predictions with form switch stories
            events.append(UserUtteranceReverted())
            # trigger utter_ask_{form}_AA_CONTINUE_FORM, by making it the requested_slot
            events.append(SlotSet("AA_CONTINUE_FORM", None))
            # # avoid that bot goes in listen mode after UserUtteranceReverted
            events.append(FollowupAction(active_form_name))

        return events

class ActionLoanAppraisal(Action):
    """Lists the contents of then known_recipients slot"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "action_loan_appraisal"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        """Executes the custom action"""
        dispatcher.utter_message(
            response="utter_loan_appraisal",
        )
		
        events = []
        active_form_name = tracker.active_form.get("name")
        if active_form_name: 
            dispatcher.utter_message(
				response="utter_ask_continue",
			)
            # keep the tracker clean for the predictions with form switch stories
            events.append(UserUtteranceReverted())
            # trigger utter_ask_{form}_AA_CONTINUE_FORM, by making it the requested_slot
            events.append(SlotSet("AA_CONTINUE_FORM", None))
            # # avoid that bot goes in listen mode after UserUtteranceReverted
            events.append(FollowupAction(active_form_name))

        return events

class ActionBadDebt(Action):
    """Lists the contents of then known_recipients slot"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "action_bad_debt"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        """Executes the custom action"""
        dispatcher.utter_message(
            response="utter_bad_debt",
        )
		
        events = []
        active_form_name = tracker.active_form.get("name")
        if active_form_name: 
            dispatcher.utter_message(
				response="utter_ask_continue",
			)
            # keep the tracker clean for the predictions with form switch stories
            events.append(UserUtteranceReverted())
            # trigger utter_ask_{form}_AA_CONTINUE_FORM, by making it the requested_slot
            events.append(SlotSet("AA_CONTINUE_FORM", None))
            # # avoid that bot goes in listen mode after UserUtteranceReverted
            events.append(FollowupAction(active_form_name))

        return events

class ActionContactInformation(Action):
    """Lists the contents of then known_recipients slot"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "action_contact_information"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        """Executes the custom action"""
        dispatcher.utter_message(
            response="utter_contact_information",
        )
		
        events = []
        active_form_name = tracker.active_form.get("name")
        if active_form_name: 
            dispatcher.utter_message(
				response="utter_ask_continue",
			)
            # keep the tracker clean for the predictions with form switch stories
            events.append(UserUtteranceReverted())
            # trigger utter_ask_{form}_AA_CONTINUE_FORM, by making it the requested_slot
            events.append(SlotSet("AA_CONTINUE_FORM", None))
            # # avoid that bot goes in listen mode after UserUtteranceReverted
            events.append(FollowupAction(active_form_name))

        return events


class ActionLoanError(Action):
    """Lists the contents of then known_recipients slot"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "action_loan_error"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        """Executes the custom action"""
        dispatcher.utter_message(
            response="utter_loan_error",
        )
		
        events = []
        active_form_name = tracker.active_form.get("name")
        if active_form_name: 
            dispatcher.utter_message(
				response="utter_ask_continue",
			)
            # keep the tracker clean for the predictions with form switch stories
            events.append(UserUtteranceReverted())
            # trigger utter_ask_{form}_AA_CONTINUE_FORM, by making it the requested_slot
            events.append(SlotSet("AA_CONTINUE_FORM", None))
            # # avoid that bot goes in listen mode after UserUtteranceReverted
            events.append(FollowupAction(active_form_name))

        return events

class ActionNotAccept(Action):
    """Lists the contents of then known_recipients slot"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "action_not_accept"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        """Executes the custom action"""
        dispatcher.utter_message(
            response="utter_not_accept",
        )
		
        events = []
        active_form_name = tracker.active_form.get("name")
        if active_form_name: 
            dispatcher.utter_message(
				response="utter_ask_continue",
			)
            # keep the tracker clean for the predictions with form switch stories
            events.append(UserUtteranceReverted())
            # trigger utter_ask_{form}_AA_CONTINUE_FORM, by making it the requested_slot
            events.append(SlotSet("AA_CONTINUE_FORM", None))
            # # avoid that bot goes in listen mode after UserUtteranceReverted
            events.append(FollowupAction(active_form_name))

        return events

class ActionDeptCollectionPolicy(Action):
    """Lists the contents of then known_recipients slot"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "action_debt_collection_policy"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        """Executes the custom action"""
        dispatcher.utter_message(
            response="utter_debt_collection_policy",
        )
		
        events = []
        active_form_name = tracker.active_form.get("name")
        if active_form_name: 
            dispatcher.utter_message(
				response="utter_ask_continue",
			)
            # keep the tracker clean for the predictions with form switch stories
            events.append(UserUtteranceReverted())
            # trigger utter_ask_{form}_AA_CONTINUE_FORM, by making it the requested_slot
            events.append(SlotSet("AA_CONTINUE_FORM", None))
            # # avoid that bot goes in listen mode after UserUtteranceReverted
            events.append(FollowupAction(active_form_name))

        return events


class ActionIncomeCondition(Action):
    """Lists the contents of then known_recipients slot"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "action_income_condition"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        """Executes the custom action"""
        dispatcher.utter_message(
            response="utter_income_condition",
        )
		
        events = []
        active_form_name = tracker.active_form.get("name")
        if active_form_name: 
            dispatcher.utter_message(
				response="utter_ask_continue",
			)
            # keep the tracker clean for the predictions with form switch stories
            events.append(UserUtteranceReverted())
            # trigger utter_ask_{form}_AA_CONTINUE_FORM, by making it the requested_slot
            events.append(SlotSet("AA_CONTINUE_FORM", None))
            # # avoid that bot goes in listen mode after UserUtteranceReverted
            events.append(FollowupAction(active_form_name))

        return events

class ActionFillInfoRequest(Action):
    """Lists the contents of then known_recipients slot"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "action_fill_info_request"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        """Executes the custom action"""
        dispatcher.utter_message(
            response="utter_fill_info_request",
        )
		
        events = []
        active_form_name = tracker.active_form.get("name")
        if active_form_name: 
            dispatcher.utter_message(
				response="utter_ask_continue",
			)
            # keep the tracker clean for the predictions with form switch stories
            events.append(UserUtteranceReverted())
            # trigger utter_ask_{form}_AA_CONTINUE_FORM, by making it the requested_slot
            events.append(SlotSet("AA_CONTINUE_FORM", None))
            # # avoid that bot goes in listen mode after UserUtteranceReverted
            events.append(FollowupAction(active_form_name))

        return events


class ActionSurcharge(Action):
    """Lists the contents of then known_recipients slot"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "action_surcharge"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        """Executes the custom action"""
        dispatcher.utter_message(
            response="utter_surcharge",
        )
		
        events = []
        active_form_name = tracker.active_form.get("name")
        if active_form_name: 
            dispatcher.utter_message(
				response="utter_ask_continue",
			)
            # keep the tracker clean for the predictions with form switch stories
            events.append(UserUtteranceReverted())
            # trigger utter_ask_{form}_AA_CONTINUE_FORM, by making it the requested_slot
            events.append(SlotSet("AA_CONTINUE_FORM", None))
            # # avoid that bot goes in listen mode after UserUtteranceReverted
            events.append(FollowupAction(active_form_name))

        return events


class ActionMortgage(Action):
    """Lists the contents of then known_recipients slot"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "action_mortgage"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        """Executes the custom action"""
        dispatcher.utter_message(
            response="utter_mortgage",
        )
		
        events = []
        active_form_name = tracker.active_form.get("name")
        if active_form_name: 
            dispatcher.utter_message(
				response="utter_ask_continue",
			)
            # keep the tracker clean for the predictions with form switch stories
            events.append(UserUtteranceReverted())
            # trigger utter_ask_{form}_AA_CONTINUE_FORM, by making it the requested_slot
            events.append(SlotSet("AA_CONTINUE_FORM", None))
            # # avoid that bot goes in listen mode after UserUtteranceReverted
            events.append(FollowupAction(active_form_name))

        return events

class ActionLoanSecurity(Action):
    """Lists the contents of then known_recipients slot"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "action_loan_security"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        """Executes the custom action"""
        dispatcher.utter_message(
            response="utter_loan_security",
        )
		
        events = []
        active_form_name = tracker.active_form.get("name")
        if active_form_name: 
            dispatcher.utter_message(
				response="utter_ask_continue",
			)
            # keep the tracker clean for the predictions with form switch stories
            events.append(UserUtteranceReverted())
            # trigger utter_ask_{form}_AA_CONTINUE_FORM, by making it the requested_slot
            events.append(SlotSet("AA_CONTINUE_FORM", None))
            # # avoid that bot goes in listen mode after UserUtteranceReverted
            events.append(FollowupAction(active_form_name))

        return events

class ActionDisbursement(Action):
    """Lists the contents of then known_recipients slot"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "action_disbursement"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        """Executes the custom action"""
        dispatcher.utter_message(
            response="utter_disbursement",
        )
		
        events = []
        active_form_name = tracker.active_form.get("name")
        if active_form_name: 
            dispatcher.utter_message(
				response="utter_ask_continue",
			)
            # keep the tracker clean for the predictions with form switch stories
            events.append(UserUtteranceReverted())
            # trigger utter_ask_{form}_AA_CONTINUE_FORM, by making it the requested_slot
            events.append(SlotSet("AA_CONTINUE_FORM", None))
            # # avoid that bot goes in listen mode after UserUtteranceReverted
            events.append(FollowupAction(active_form_name))

        return events

class ActionContractInformation(Action):
    """Lists the contents of then known_recipients slot"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "action_contract_information"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        """Executes the custom action"""
        dispatcher.utter_message(
            response="utter_contract_information",
        )
		
        events = []
        active_form_name = tracker.active_form.get("name")
        if active_form_name: 
            dispatcher.utter_message(
				response="utter_ask_continue",
			)
            # keep the tracker clean for the predictions with form switch stories
            events.append(UserUtteranceReverted())
            # trigger utter_ask_{form}_AA_CONTINUE_FORM, by making it the requested_slot
            events.append(SlotSet("AA_CONTINUE_FORM", None))
            # # avoid that bot goes in listen mode after UserUtteranceReverted
            events.append(FollowupAction(active_form_name))

        return events

class ActionInterestPaymentPeriod(Action):
    """Lists the contents of then known_recipients slot"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "action_interest_payment_period"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        """Executes the custom action"""
        dispatcher.utter_message(
            response="utter_interest_payment_period",
        )
		
        events = []
        active_form_name = tracker.active_form.get("name")
        if active_form_name: 
            dispatcher.utter_message(
				response="utter_ask_continue",
			)
            # keep the tracker clean for the predictions with form switch stories
            events.append(UserUtteranceReverted())
            # trigger utter_ask_{form}_AA_CONTINUE_FORM, by making it the requested_slot
            events.append(SlotSet("AA_CONTINUE_FORM", None))
            # # avoid that bot goes in listen mode after UserUtteranceReverted
            events.append(FollowupAction(active_form_name))

        return events

class ActionBorrower(Action):
    """Lists the contents of then known_recipients slot"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "action_borrower"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        """Executes the custom action"""
        dispatcher.utter_message(
            response="utter_borrower",
        )
		
        events = []
        active_form_name = tracker.active_form.get("name")
        if active_form_name: 
            dispatcher.utter_message(
				response="utter_ask_continue",
			)
            # keep the tracker clean for the predictions with form switch stories
            events.append(UserUtteranceReverted())
            # trigger utter_ask_{form}_AA_CONTINUE_FORM, by making it the requested_slot
            events.append(SlotSet("AA_CONTINUE_FORM", None))
            # # avoid that bot goes in listen mode after UserUtteranceReverted
            events.append(FollowupAction(active_form_name))

        return events

class ActionCicIntroduce(Action):
    """Lists the contents of then known_recipients slot"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "action_cic_introduce"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        """Executes the custom action"""
        dispatcher.utter_message(
            response="utter_cic_introduce",
        )
		
        events = []
        active_form_name = tracker.active_form.get("name")
        if active_form_name: 
            dispatcher.utter_message(
				response="utter_ask_continue",
			)
            # keep the tracker clean for the predictions with form switch stories
            events.append(UserUtteranceReverted())
            # trigger utter_ask_{form}_AA_CONTINUE_FORM, by making it the requested_slot
            events.append(SlotSet("AA_CONTINUE_FORM", None))
            # # avoid that bot goes in listen mode after UserUtteranceReverted
            events.append(FollowupAction(active_form_name))

        return events

class ActionBot(Action):
    """Lists the contents of then known_recipients slot"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "action_bot"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        """Executes the custom action"""
        dispatcher.utter_message(
            response="utter_bot",
        )
		
        events = []
        active_form_name = tracker.active_form.get("name")
        if active_form_name: 
            dispatcher.utter_message(
				response="utter_ask_continue",
			)
            # keep the tracker clean for the predictions with form switch stories
            events.append(UserUtteranceReverted())
            # trigger utter_ask_{form}_AA_CONTINUE_FORM, by making it the requested_slot
            events.append(SlotSet("AA_CONTINUE_FORM", None))
            # # avoid that bot goes in listen mode after UserUtteranceReverted
            events.append(FollowupAction(active_form_name))

        return events

class ActionExclamationSentence(Action):
    """Lists the contents of then known_recipients slot"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "action_exclamation_sentence"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        """Executes the custom action"""
        dispatcher.utter_message(
            response="utter_exclamation_sentence",
        )
		
        events = []
        active_form_name = tracker.active_form.get("name")
        if active_form_name: 
            dispatcher.utter_message(
				response="utter_ask_continue",
			)
            # keep the tracker clean for the predictions with form switch stories
            events.append(UserUtteranceReverted())
            # trigger utter_ask_{form}_AA_CONTINUE_FORM, by making it the requested_slot
            events.append(SlotSet("AA_CONTINUE_FORM", None))
            # # avoid that bot goes in listen mode after UserUtteranceReverted
            events.append(FollowupAction(active_form_name))

        return events


class ActionCheckLoanAmount(Action):
    """Lists the contents of then known_recipients slot"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "action_check_loan_amount"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        """Executes the custom action"""
        amount_of_money = float(tracker.get_slot('number'))
        if amount_of_money > 5000000:
            dispatcher.utter_message(
                text="Rất tiếc, hiện nay công ty em chỉ cho vay tối đa là 5 triệu đồng",
            )
        else:
            dispatcher.utter_message(
                text="Dạ được ạ. Anh chị vui lòng vào [link đăng kí](https://www.vndcredit.vn) để điền các thông tin cần thiết để thực hiện khoản vay.",
            )
		
        events = []
        active_form_name = tracker.active_form.get("name")
        if active_form_name: 
            dispatcher.utter_message(
				response="utter_ask_continue",
			)
            # keep the tracker clean for the predictions with form switch stories
            events.append(UserUtteranceReverted())
            # trigger utter_ask_{form}_AA_CONTINUE_FORM, by making it the requested_slot
            events.append(SlotSet("AA_CONTINUE_FORM", None))
            # # avoid that bot goes in listen mode after UserUtteranceReverted
            events.append(FollowupAction(active_form_name))

        return events


class ActionVerifyUserConfirm(Action):
    """Lists the contents of then known_recipients slot"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "action_verify_user_confirm"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        """Executes the custom action"""
        amount_of_money = next(tracker.get_latest_entity_values("number"), None)
        if amount_of_money!= None:
            if float(amount_of_money) <= 5000000:
                dispatcher.utter_message(
                    response="utter_verify_user_confirm",
                )
            else:
                dispatcher.utter_message(
                    response="utter_verify_number_of_money",
                )
        else:
            dispatcher.utter_message(
                response="utter_verify_user_confirm",
            )
        events = []
        active_form_name = tracker.active_form.get("name")
        if active_form_name: 
            dispatcher.utter_message(
				response="utter_ask_continue",
			)
            # keep the tracker clean for the predictions with form switch stories
            events.append(UserUtteranceReverted())
            # trigger utter_ask_{form}_AA_CONTINUE_FORM, by making it the requested_slot
            events.append(SlotSet("AA_CONTINUE_FORM", None))
            # # avoid that bot goes in listen mode after UserUtteranceReverted
            events.append(FollowupAction(active_form_name))

        return events

class ActionSad(Action):
    """Lists the contents of then known_recipients slot"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "action_sad"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        """Executes the custom action"""
        dispatcher.utter_message(
            response="utter_sad",
        )
		
        events = []
        active_form_name = tracker.active_form.get("name")
        if active_form_name: 
            dispatcher.utter_message(
				response="utter_ask_continue",
			)
            # keep the tracker clean for the predictions with form switch stories
            events.append(UserUtteranceReverted())
            # trigger utter_ask_{form}_AA_CONTINUE_FORM, by making it the requested_slot
            events.append(SlotSet("AA_CONTINUE_FORM", None))
            # # avoid that bot goes in listen mode after UserUtteranceReverted
            events.append(FollowupAction(active_form_name))

        return events


class ActionNotPaid(Action):
    """Lists the contents of then known_recipients slot"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "action_not_paid"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        """Executes the custom action"""
        dispatcher.utter_message(
            response="utter_not_paid",
        )
		
        events = []
        active_form_name = tracker.active_form.get("name")
        if active_form_name: 
            dispatcher.utter_message(
				response="utter_ask_continue",
			)
            # keep the tracker clean for the predictions with form switch stories
            events.append(UserUtteranceReverted())
            # trigger utter_ask_{form}_AA_CONTINUE_FORM, by making it the requested_slot
            events.append(SlotSet("AA_CONTINUE_FORM", None))
            # # avoid that bot goes in listen mode after UserUtteranceReverted
            events.append(FollowupAction(active_form_name))

        return events

class ActionHelp(Action):
    """Lists the contents of then known_recipients slot"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "action_help"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        """Executes the custom action"""
        dispatcher.utter_message(
            response="utter_help",
        )
		
        events = []
        active_form_name = tracker.active_form.get("name")
        if active_form_name: 
            dispatcher.utter_message(
				response="utter_ask_continue",
			)
            # keep the tracker clean for the predictions with form switch stories
            events.append(UserUtteranceReverted())
            # trigger utter_ask_{form}_AA_CONTINUE_FORM, by making it the requested_slot
            events.append(SlotSet("AA_CONTINUE_FORM", None))
            # # avoid that bot goes in listen mode after UserUtteranceReverted
            events.append(FollowupAction(active_form_name))

        return events

class ActionNotInterest(Action):
    """Lists the contents of then known_recipients slot"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "action_not_interest"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        """Executes the custom action"""
        dispatcher.utter_message(
            response="utter_not_interest",
        )
		
        events = []
        active_form_name = tracker.active_form.get("name")
        if active_form_name: 
            dispatcher.utter_message(
				response="utter_ask_continue",
			)
            # keep the tracker clean for the predictions with form switch stories
            events.append(UserUtteranceReverted())
            # trigger utter_ask_{form}_AA_CONTINUE_FORM, by making it the requested_slot
            events.append(SlotSet("AA_CONTINUE_FORM", None))
            # # avoid that bot goes in listen mode after UserUtteranceReverted
            events.append(FollowupAction(active_form_name))

        return events