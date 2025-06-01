from flask import Flask, render_template, redirect, url_for, request
from utils import generate_user_id, generate_qr_code, Blockchain, SmartContract
from forms import RegistrationForm, LoginForm, LabSubmissionForm
from datetime import datetime
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecretkey'

blockchain = Blockchain()
smart_contract = SmartContract()

@app.route("/", methods=["GET"])
def home():
    return render_template("home.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user_data = {
            'type': 'registration',
            'name': form.name.data,
            'national_id': form.national_id.data,
            'phone': form.phone.data,
            'birth_date': form.birth_date.data.strftime('%Y-%m-%d'),
            'profession': form.profession.data
        }
        is_valid, message = smart_contract.validate_registration(user_data, blockchain)
        if not is_valid:
            return render_template("register.html", form=form, error=message)

        user_id = generate_user_id()
        user_data['user_id'] = user_id
        qr_path = generate_qr_code(user_id)
        blockchain.add_block(user_data)
        return render_template("user_profile.html", user_id=user_id, qr_path=qr_path)

    return render_template("register.html", form=form)

@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user_id = form.user_id.data
        profession = form.profession.data
        if profession == 'doctor':
            return redirect(url_for('doctor', user_id=user_id))
        elif profession == 'patient':
            return redirect(url_for('patient', user_id=user_id))
        elif profession == 'pharmacist':
            return redirect(url_for('pharmacist', user_id=user_id))
        elif profession == 'lab':
            return redirect(url_for('lab', user_id=user_id))
    return render_template('login.html', form=form)

@app.route('/doctor/<user_id>', methods=["GET", "POST"])
def doctor(user_id):
    if request.method == "POST":
        form_type = request.form.get("form_type")

        if form_type == "patient_form":
            patient_id = request.form.get("patient_id")
            diagnosis = request.form.get("diagnosis")
            prescription = request.form.get("prescription")
            file = request.files.get("medical_docs")

            if not all([patient_id, diagnosis, prescription, file]):
                return render_template("doctor.html", user_id=user_id, error="Missing fields")

            filename = secure_filename(file.filename)
            upload_dir = os.path.join("static", "uploads")
            os.makedirs(upload_dir, exist_ok=True)
            file_path = os.path.join(upload_dir, filename)
            file.save(file_path)

            doc_data = {
                "type": "medical_document",
                "submitted_by": user_id,
                "patient_id": patient_id,
                "document_type": "diagnosis",
                "diagnosis": diagnosis,
                "prescription": prescription,
                "file_name": filename,
                "file_url": f"/static/uploads/{filename}",
                "upload_date": datetime.now().isoformat()
            }
            blockchain.add_block(doc_data)
            return render_template("doctor.html", user_id=user_id, success="Patient info and document uploaded.")

        elif form_type == "lab_form":
            lab_id = request.form.get("lab_id")
            Sample_Type = request.form.get("Sample_Type")
            Test_Instructions = request.form.get("Test_Instructions")
            file = request.files.get("lab_file")

            if not all([lab_id, Sample_Type, Test_Instructions, file]):
                return render_template("doctor.html", user_id=user_id, error="Missing lab fields")

            filename = secure_filename(file.filename)
            upload_dir = os.path.join("static", "uploads")
            os.makedirs(upload_dir, exist_ok=True)
            file_path = os.path.join(upload_dir, filename)
            file.save(file_path)

            lab_data = {
                "type": "lab_submission",
                "submitted_by": user_id,
                "lab_id": lab_id,
                "Sample Type": Sample_Type,
                "Test Instructions": Test_Instructions,
                "file_name": filename,
                "file_url": f"/static/uploads/{filename}",
                "upload_date": datetime.now().isoformat()
            }
            blockchain.add_block(lab_data)
            return render_template("doctor.html", user_id=user_id, success="Lab data uploaded")

        elif form_type == "pharmacy_form":
            pharmacy_id = request.form.get("pharmacy_id")
            medications = request.form.get("medications")
            file = request.files.get("pharmacy_file")

            if not all([pharmacy_id, medications, file]):
                return render_template("doctor.html", user_id=user_id, error="Missing pharmacy fields")

            filename = secure_filename(file.filename)
            upload_dir = os.path.join("static", "uploads")
            os.makedirs(upload_dir, exist_ok=True)
            file_path = os.path.join(upload_dir, filename)
            file.save(file_path)

            pharmacy_data = {
                "type": "pharmacy_submission",
                "submitted_by": user_id,
                "pharmacy_id": pharmacy_id,
                "medications": medications,
                "file_name": filename,
                "file_url": f"/static/uploads/{filename}",
                "upload_date": datetime.now().isoformat()
            }
            blockchain.add_block(pharmacy_data)
            return render_template("doctor.html", user_id=user_id, success="Pharmacy data uploaded")

    lab_results = [
        block.data for block in blockchain.chain
        if block.data.get("type") == "lab_submission" and block.data.get("doctor_id") == user_id
    ]

    pharmacy_confirmations = [
        block.data for block in blockchain.chain
        if block.data.get("type") == "delivery_confirmation" and block.data.get("doctor_id") == user_id and "pharmacy_id" in block.data
    ]

    patient_messages = [
        block.data for block in blockchain.chain
        if block.data.get("type") == "patient_question" and block.data.get("doctor_id") == user_id and "patient_id" in block.data
    ]

    return render_template("doctor.html", user_id=user_id,
                           lab_results=lab_results,
                           pharmacy_confirmations=pharmacy_confirmations,
                           patient_messages=patient_messages)

@app.route('/patient/<user_id>')
def patient(user_id):
    patient_documents = [
        block.data for block in blockchain.chain
        if block.data.get("type") == "medical_document" and block.data.get("patient_id") == user_id
    ]
    return render_template('patient.html', user_id=user_id, documents=patient_documents)

@app.route('/patient_question', methods=['POST'])
def patient_question():
    patient_id = request.form['patient_id']
    doctor_id = request.form['doctor_id']
    question = request.form['question']

    question_data = {
        "type": "patient_question",
        "patient_id": patient_id,
        "doctor_id": doctor_id,
        "question": question,
        "confirmation_date": datetime.utcnow().isoformat()
    }

    blockchain.add_block(data=question_data)
    return redirect(url_for('patient', user_id=patient_id))

@app.route('/pharmacist/<user_id>')
def pharmacist(user_id):
    pharmacist_documents = [
        block.data for block in blockchain.chain
        if block.data.get("type") == "pharmacy_submission" and block.data.get("pharmacy_id") == user_id
    ]
    return render_template('pharmacist.html', user_id=user_id, documents=pharmacist_documents)

@app.route('/confirm_delivery', methods=['POST'])
def confirm_delivery():
    pharmacy_id = request.form['pharmacy_id']
    doctor_id = request.form['doctor_id']
    medications = request.form['medications']

    delivery_data = {
        "type": "delivery_confirmation",
        "pharmacy_id": pharmacy_id,
        "doctor_id": doctor_id,
        "medications": medications,
        "confirmation_date": datetime.utcnow().isoformat()
    }

    blockchain.add_block(data=delivery_data)
    return redirect(url_for('pharmacist', user_id=pharmacy_id))

@app.route('/lab/<user_id>', methods=["GET", "POST"])
def lab(user_id):
    lab_documents = [
        block.data for block in blockchain.chain
        if block.data.get("type") == "lab_submission" and block.data.get("lab_id") == user_id
    ]

    form = LabSubmissionForm()
    if form.validate_on_submit():
        submission_data = {
            'type': 'lab_submission',
            'lab_id': user_id,
            'test_type': form.test_type.data,
            'result': form.result.data,
            'submission_date': datetime.now().isoformat()
        }
        is_valid, message = smart_contract.validate_lab_submission(submission_data, blockchain)
        if not is_valid:
            return render_template("lab.html", form=form, user_id=user_id, error=message)
        blockchain.add_block(submission_data)
        return render_template("lab.html", form=form, user_id=user_id, success="Lab submission recorded")

    return render_template('lab.html', form=form, user_id=user_id, blockchain_data=lab_documents)

@app.route("/lab_send_data", methods=["POST"])
def lab_send_data():
    doctor_id = request.form['doctor_id']
    lab_id = request.form['lab_id']
    result = request.form['result']
    file = request.files.get("file")

    if not all([doctor_id, lab_id, result, file]):
        return "Missing fields", 400

    filename = secure_filename(file.filename)
    upload_dir = os.path.join("static", "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, filename)
    file.save(file_path)

    data = {
        "type": "lab_submission",
        "submitted_by": lab_id,
        "doctor_id": doctor_id,
        "result": result,
        "file_name": filename,
        "document_url": f"/static/uploads/{filename}",
        "submission_date": datetime.now().isoformat()
    }
    blockchain.add_block(data)
    return redirect(url_for("lab", user_id=lab_id))

@app.route("/blockchain")
def blockchain_view():
    return render_template("blockchain.html", blockchain=blockchain.chain)

if __name__ == "__main__":
    app.run(debug=True)
