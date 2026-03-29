from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os, json

app = Flask(__name__)

# تحديد المسار الأساسي للمشروع لضمان وصول السيرفر لقاعدة البيانات والصور
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'ridanaa.db')
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'static/uploads')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# الجداول
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name_ar = db.Column(db.String(100))
    name_en = db.Column(db.String(100))
    price = db.Column(db.Float)
    images_json = db.Column(db.Text)
    inventory_json = db.Column(db.Text)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    items = db.Column(db.Text)
    status = db.Column(db.String(20), default="قيد الانتظار")

# إنشاء قاعدة البيانات وفولدر الرفع تلقائياً عند التشغيل
with app.app_context():
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    db.create_all()

@app.route('/')
def index():
    try:
        products = Product.query.all()
        p_list = []
        for p in products:
            p_list.append({
                "id": p.id,
                "nameAr": p.name_ar,
                "nameEn": p.name_en,
                "price": p.price,
                "imgs": json.loads(p.images_json) if p.images_json else [],
                "inventory": json.loads(p.inventory_json) if p.inventory_json else {}
            })
        return render_template('index.html', products_json=json.dumps(p_list))
    except Exception as e:
        return f"Error: {str(e)}" # بيساعدنا نعرف المشكلة لو حصلت بدل صفحة Error 500 البيضاء

@app.route('/admin')
def admin():
    return render_template('admin.html', products=Product.query.all(), orders=Order.query.all())

@app.route('/admin/save', methods=['POST'])
def save_product():
    p_id = request.form.get('p_id')
    inv = json.dumps({s: int(request.form.get(f'qty_{s}', 0)) for s in ['S','M','L','XL']})
    files = request.files.getlist('images')
    
    saved = []
    if files and files[0].filename != '':
        for f in files:
            # حفظ الصورة في المسار الكامل الصحيح
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], f.filename))
            saved.append('/static/uploads/' + f.filename)
    
    if p_id: # تعديل
        p = Product.query.get(p_id)
        p.name_ar, p.name_en, p.price, p.inventory_json = request.form['name_ar'], request.form['name_en'], float(request.form['price']), inv
        if saved: p.images_json = json.dumps(saved)
    else: # إضافة جديد
        new_p = Product(name_ar=request.form['name_ar'], name_en=request.form['name_en'], price=float(request.form['price']), images_json=json.dumps(saved), inventory_json=inv)
        db.session.add(new_p)
    
    db.session.commit()
    return redirect('/admin')

@app.route('/admin/delete/<int:id>')
def delete_p(id):
    p = Product.query.get(id)
    if p:
        db.session.delete(p)
        db.session.commit()
    return redirect('/admin')

@app.route('/order', methods=['POST'])
def create_order():
    data = request.json
    db.session.add(Order(name=data['name'], phone=data['phone'], address=data['address'], items=data['items']))
    db.session.commit()
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(debug=True)
