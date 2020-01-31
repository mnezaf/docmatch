import streamlit as st
import pandas as pd
import pickle
import matplotlib.pyplot as plt
#from model import predict
from collections import OrderedDict

st.title("Specialist Recommendation")
st.warning("Please check your insurance policy before making appointment with recommended specialist!")
SEX = st.selectbox('Sex', ('male','female'))
AGE = st.text_input('Birth Year')

gen = st.multiselect("General Symptoms",('fever', 'fatigue', "insomnia", "memory loss","altered mental status","other"))
nerv= st.multiselect("Nervous Symptoms",('disturbance of smell or taste' , 'abnormal posture', "facial weekness","lack of coordination","other"))
cardio = st.multiselect("Cardiovascular Symptoms", ('Tachycardia', 'abnormal sounds', "shock", "other"))
dig = st.multiselect("Digestive Symptoms", ('nausea', 'vomiting', "heart burn", "gas bloating", "other"))
sk = st.multiselect("Skin Symptoms", ('rash', 'edema', "change in texture","swelling","other"))
nut = st.multiselect("Nutrition Symptoms", ('weight gain', 'weight loss', "feeding difficulties", "other"))
head= st.multiselect("HEad and Neck Symptoms", ('headache', 'throat pain', "voice disturbance", "other"))
resp = st.multiselect("Respiratory Symptoms", ('apnea', 'chest pain', "abnormal sound", "cough", "shortness of breath","other"))
ur= st.multiselect("Urinary Symptoms", ('', '', "", "", ""))
abd = st.multiselect("Abdominal Symptoms", ('', '', "", "", ""))
urin = st.multiselect("Urine Symptoms", ('', '', "", "", ""))
bld = st.multiselect("Blood Symptoms", ('abnormal glucose', '', "", "", ""))
stool = st.multiselect("Stool Symptoms", ('', '', "", "", ""))
rad = st.multiselect("Radiological Symptoms", ('', '', "", "", ""))
im = st.multiselect("Immunological Symptoms", ('', '', "", "", ""))
oth = st.multiselect("Other Symptoms", ('', '', "", "", ""))


if st.button("Submit"):
    d = {780:gen,781:nerv,782:sk,783:nut,784:head,785:cardio,786:resp,787:dig,788:ur,789:abd,790:bld,791:urin,792:stool,793:rad,795:im,796: oth}
    ll=[0]*(799-780+1)
#    dict=OrderedDict()
    for k in range(780,800):
        dict[k]=0
    for k in d.keys():
        dict[k]+=len(d[k])
    testdf = pd.DataFrame()
    testdf = testdf.append(dict, ignore_index=True)
    s=2
    if (SEX=="male"):
        s=1

    testdf["SEX"]=s
    testdf["DOBYY"]= int(AGE)

    dd = {1: "ALLERGY/IMMUNOLOGY", 2: "ANESTHESIOLOGY", 3: "CARDIOLOGY", 4: "DERMATOLOGY", \
         5: "ENDOCRINOLOGY/METABOLISM", 6: "FAMILY PRACTICE", 7: "GASTROENTEROLOGY", \
         8: "GENERAL PRACTICE", 9: "GENERAL SURGERY", 10: "GERIATRICS", 11: "GYNECOLOGY/OBSTETRICS", \
         12: "HEMATOLOGY", 13: "HOSPITAL RESIDENCE", 14: "INTERNAL MEDICINE", 15: "NEPHROLOGY", \
         16: "NEUROLOGY", 17: "NUCLEAR MEDICINE", 18: "ONCOLOGY", 19: "OPHTHALMOLOGY", 20: "ORTHOPEDICS",
         21: "OSTEOPATHY", \
         22: "OTORHINOLARYNGOLOGY", 23: "PATHOLOGY", 24: "PEDIATRICIAN", 25: "PHYSICAL MEDICINE/REHAB", \
         26: "PLASTIC SURGERY", 27: "PROCTOLOGY", 28: "PSYCHIATRY", \
         29: "PULMONARY", 30: "RADIOLOGY", 31: "RHEUMATOLOGY", 32: "THORACIC SURGERY", \
         33: "UROLOGY"}

    logisticRegr = pickle.load(open("/Users/parya/PycharmProjects/InsightProject/specialist_classifier_logReg_MEPS", 'rb'))
    labels = pickle.load(open("/Users/parya/PycharmProjects/InsightProject/labels", 'rb'))
    prob = logisticRegr.predict_proba(testdf)
    predictions = logisticRegr.predict(testdf)
    st.write("You should see a %s specialist"%dd[predictions[0]])
    plt.rcParams["figure.figsize"] = (20, 15)
    plt.rcParams.update({'font.size': 22})
    plt.bar(labels, prob[0, :])
    plt.xticks(rotation='vertical',)

    st.pyplot()



 #  predictions = predict(...)
  #  result = InsightProject.py  # run our function  on it
   # st.balloons()  # show some cool animation
 #   st.success(result)  # show result in a Bootstrap panel


#predictions = logisticRegr.predict(testdf)


