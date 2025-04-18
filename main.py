import streamlit as st
import pandas as pd
import time
import data_access_layer as dal

from authentication import authenticate
from datetime import datetime

st.markdown("""
<style>
/* Apply RTL globally */
html, body, [data-testid="stAppViewContainer"] {
    direction: rtl;
    unicode-bidi: bidi-override;
    text-align: right;
}

/* Override RTL for dataframes */
[data-testid="stDataFrame"] {
    direction: ltr !important;
    text-align: left !important;
}
</style>
""", unsafe_allow_html=True)





def display_dataframe(data: pd.DataFrame, editable = False):
	st.dataframe(data, column_config={
		"תאריך": st.column_config.DateColumn(format="DD.MM.YYYY"),
	},
	hide_index=True)



def handle_reciepts():
	u_data = dal.get_all_donations(reciepted=False)
	r_data = dal.get_all_donations(reciepted=True)

	if len(u_data) > 0:
		u_data["מספר פנקס"] = u_data["מספר פנקס"].astype(str)
		u_data["מספר קבלה"] = u_data["מספר קבלה"].astype(str)

		uneditables = u_data.columns.tolist()
		uneditables.remove("קבלה")
		uneditables.remove("מספר פנקס")
		uneditables.remove("מספר קבלה")

		u_data = st.data_editor(u_data, disabled=uneditables, column_config={
			"תאריך": st.column_config.DateColumn(format="DD.MM.YYYY"),
		},
		hide_index=True)

		if st.button("שמור"):
			st.session_state["DONATIONS"] = pd.concat([u_data, r_data])
			dal.mark_donations(st.session_state["DONATIONS"])

			st.session_state["reciepts_submitted"] = True
	else:
		st.success("אין על מה להוציא קבלות!!")
	
def handle_purchase():
	date = st.date_input("תאריך", format="DD.MM.YYYY")
	year = st.text_input("שנה", value=dal.get_last_yesr())
	day = st.text_input("פרשה")

	name = st.selectbox("שם", options=dal.get_all_people() + ["חדש"], index=None, placeholder="בחר מתפלל", key=f"name {st.session_state['purchase_key']}")
	if name == "חדש":
		new_name = st.text_input("שם", placeholder="מתפלל חדש", key=f"new_name {st.session_state['purchase_key']}")
	else:
		new_name = None  # to keep variable defined

	if name != None:
		mitsva = st.selectbox("מצוה", options=st.session_state["MITZVOT"], index=None, key=f"mitsva {st.session_state['purchase_key']}")
		amount = st.number_input("סכום", step=1, key=f"amount {st.session_state['purchase_key']}")

		if st.button("שמור"):
			final_name = name if name != "חדש" else new_name
			purchase = {
				"תאריך" : [date],
				"שנה" : [year],
				"פרשה" : [day],
				"שם" : [final_name],
				"סכום" : [amount],
				"מצוה" : [mitsva],
			}

			st.session_state["PURCHASES"] = pd.concat([st.session_state["PURCHASES"], pd.DataFrame.from_dict(purchase)])
			dal.insert_purchase(date, year, day, final_name, amount, mitsva)

			if name == "חדש":
				dal.add_new_person(new_name)
				st.session_state["PEOPLE"].append(new_name)

			st.session_state["purchase_key"] += 1
			st.session_state["purchase_submitted"] = True

def handle_donation():
	name = st.selectbox("שם", options=dal.get_all_people() + ["חדש"], index=None, placeholder="בחר מתפלל", key=f"name {st.session_state['purchase_key']}")

	if name == "חדש":
		new_name = st.text_input("שם", placeholder="מתפלל חדש")
	else:
		new_name = None  # to keep variable defined

	if name != None:
		date = st.date_input("תאריך", format="DD.MM.YYYY")
		year = st.text_input("שנה", value=dal.get_last_yesr())
		amount = st.number_input("סכום", step=1)
		method = st.selectbox("אופן תשלום", options=st.session_state["PAYMENT_METHODS"])
		has_reciept = st.checkbox("האם ניתנה קבלה?")

		book = " "
		reciept = " "

		if has_reciept:
			book = st.text_input("מספר פנקס")
			reciept = st.text_input("מספר קבלה")

		if st.button("שמור"):
			final_name = name if name != "חדש" else new_name
			donation = {
				"תאריך" : [date],
				"שנה" : [year],
				"שם" : [final_name],
				"סכום" : [amount],
				"אופן תשלום": [method],
				"קבלה" : [has_reciept],
				"מספר פנקס" : [book],
				"מספר קבלה" : [reciept],
			}


			st.session_state["DONATIONS"] = pd.concat([st.session_state["DONATIONS"], pd.DataFrame.from_dict(donation)])
			dal.insert_donation(date, year, final_name, amount, method, has_reciept, book, reciept)

			if name == "חדש":
				dal.add_new_person(new_name)
				st.session_state["PEOPLE"].append(new_name)

			st.session_state["donation_submitted"] = True



def get_report_by_person(name: str, year: str = None):
	if year:
		yearly_purchases_report = st.session_state["PURCHASES"][(st.session_state["PURCHASES"]["שם"] == name) & (st.session_state["PURCHASES"]["שנה"] == year)].drop("שם", axis=1)
		yearly_donations_report = st.session_state["DONATIONS"][(st.session_state["DONATIONS"]["שם"] == name) & (st.session_state["DONATIONS"]["שנה"] == year)].drop("שם", axis=1)

		previous_purchases_report = st.session_state["PURCHASES"][(st.session_state["PURCHASES"]["שם"] == name) & (st.session_state["PURCHASES"]["שנה"] < year)].drop("שם", axis=1)
		previous_donations_report = st.session_state["DONATIONS"][(st.session_state["DONATIONS"]["שם"] == name) & (st.session_state["DONATIONS"]["שנה"] < year)].drop("שם", axis=1)


		yearly_purchases_sum = yearly_purchases_report["סכום"].sum()
		yearly_donations_sum = yearly_donations_report["סכום"].sum()
		previous_purchases_sum = previous_purchases_report["סכום"].sum()
		previous_donations_sum = previous_donations_report["סכום"].sum()
		
		yearly_total = yearly_donations_sum - yearly_purchases_sum
		previous_total = previous_donations_sum - previous_purchases_sum

		total_sum = yearly_total + previous_total

		general_report = {
			'יתרה משנה קודמת': [previous_total],
			'תרומות שנה נוכחית': [yearly_donations_sum],
			'חובות שנה נוכחית': [yearly_purchases_sum],
			'סך הכל שנה נוכחית': [previous_total],
			'סך הכל': [total_sum],
		}

		general_report = pd.DataFrame.from_dict(general_report)
		return (general_report, yearly_donations_report, yearly_purchases_report)
	else:
		purchases_report = st.session_state["PURCHASES"][st.session_state["PURCHASES"]["שם"] == name].drop("שם", axis=1)
		donations_report = st.session_state["DONATIONS"][st.session_state["DONATIONS"]["שם"] == name].drop("שם", axis=1)

		purchases_sum = purchases_report["סכום"].sum()
		donations_sum = donations_report["סכום"].sum()
		
		total = donations_sum - purchases_sum

		general_report = {
			'תרומות': [donations_sum],
			'חובות': [purchases_sum],
			'סך הכל': [total],
		}

		general_report = pd.DataFrame.from_dict(general_report)
		return (general_report, donations_report, purchases_report)

def get_report_by_day(year: str, day: str):
	report = st.session_state["PURCHASES"][(st.session_state["PURCHASES"]["שנה"] == year) & (st.session_state["PURCHASES"]["פרשה"].str.contains(day))]
	date = datetime.strftime(report["תאריך"].tolist()[0], "%d.%m.%Y")
	message = f"פרשת {day}, {year}, {date}"

	if len(set(report["פרשה"].tolist())) == 1:
		return (report.drop(["תאריך", "שנה", "פרשה"], axis=1), message, report["סכום"].sum())
	else:
		return (report.drop(["תאריך", "שנה"], axis=1), message, report["סכום"].sum())

def get_general_report():
	people = dal.get_all_people()
	money_owed = 0

	names, debts = [], []
	for person in people:
		report, _, _ = get_report_by_person(person)
		
		balance = float(report["סך הכל"].tolist()[0])

		if balance < 0:
			money_owed += balance * -1
			names.append(person)
			debts.append(balance * -1)

	general_report = {
		"סכום": debts,
		"שם": names,
	}

	general_report = pd.DataFrame.from_dict(general_report)
	return (money_owed, general_report)




# if "logged_in" not in st.session_state:
# 	if authenticate():
# 		st.rerun()
# else:
if "purchase_key" not in st.session_state:
	st.session_state["purchase_key"] = 0
if "purchase_submitted" not in st.session_state:
	st.session_state["purchase_submitted"] = False
if "donation_submitted" not in st.session_state:
	st.session_state["donation_submitted"] = False
if "reciepts_submitted" not in st.session_state:
	st.session_state["reciepts_submitted"] = False
if "db_loaded" not in st.session_state:
	with st.spinner("אנחנו מכינים הכל... אנא התאזרו בסבלנות"):
		dal.load_db()
	st.session_state["db_loaded"] = True


actions = ["למלא דוח שבועי", "לתעד תרומה", "להוציא קבלות", "להוציא דוח"]
action = st.selectbox("מה תרצה לעשות?", options=actions, index=None, placeholder="בחר אפשרות")#, key=st.session_state["purchase_key"])

if action != None:
	if action == "למלא דוח שבועי":
		handle_purchase()

		if st.session_state["purchase_submitted"]:
			st.success("הושלם בהצלחה!")
			time.sleep(0.2)

			st.session_state["purchase_submitted"] = False

			st.rerun()
	elif action == "לתעד תרומה":
		handle_donation()

		if st.session_state["donation_submitted"]:
			st.success("הושלם בהצלחה!")
			time.sleep(0.2)

			st.session_state["purchase_key"] += 1
			st.session_state["donation_submitted"] = False

			st.rerun()
	elif action == "להוציא דוח":
		options = ["לפי אדם", "לפי פרשה", "כללי"]
		choice = st.selectbox("איזה דוח תרצה להוציא?", options=options, index=None, placeholder="בחר דוח")


		if choice == "לפי אדם":
			name = st.selectbox("על מי תרצה להוציא דוח?", options=dal.get_all_people(), index=None, placeholder="בחר אדם")
			year = st.selectbox("שנה", options=dal.get_all_years(), index=len(dal.get_all_years())-1, placeholder="בחר שנה")
			
			if name != None:
				general_report, donations_report, purchases_report = get_report_by_person(name, year)

				st.write("כללי")
				display_dataframe(general_report)

				st.write("חובות")
				display_dataframe(purchases_report)

				st.write("תרומות")
				display_dataframe(donations_report)
		elif choice == "לפי פרשה":
			year = st.selectbox("שנה", options=dal.get_all_years(), index=None, placeholder="בחר שנה")
			if year != None:
				day = st.text_input("על איזה פרשה תרצה להוציא דוח?", placeholder="בחר פרשה")

			if year != None and day != "" and st.button("הוצא דוח"):
				report, message, total = get_report_by_day(year, day)
				
				st.write(message)
				st.write(f"סכום כולל: {total:,}")
				display_dataframe(report)
		elif choice == "כללי":
			total, general_report = get_general_report()

			st.write(f"כסף בחוץ: {total:,}")
			display_dataframe(general_report)
	elif action == "להוציא קבלות":
		handle_reciepts()
		
		if st.session_state["reciepts_submitted"]:
			st.success("הושלם בהצלחה!")
			time.sleep(0.2)

			st.session_state["purchase_key"] += 1
			st.session_state["reciepts_submitted"] = False

			st.rerun()

