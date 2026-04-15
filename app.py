from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
from openpyxl import load_workbook, Workbook
import json
import os
from functools import wraps
from datetime import datetime
import io

app = Flask(__name__)
app.secret_key = 'kladka-hub-secret-2026'

@app.context_processor
def inject_now():
    return {'now': datetime.now().strftime('%d.%m.%Y')}

USERS = {
    'veduschiy': {'password': 'kh2026', 'role': 'lead', 'name': 'Ведущий инженер'},
    'inzhener': {'password': 'kh2026r', 'role': 'pricing', 'name': 'Инженер расценки'}
}

DATA_DIR = 'data'
SPRAVOCHNIK_FILE = os.path.join(DATA_DIR, 'spravochnik.xlsx')
MAPPING_FILE = os.path.join(DATA_DIR, 'mapping.json')
VOR_FILE = os.path.join(DATA_DIR, 'vor_kholodov.xlsx')


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def load_spravochnik():
    if not os.path.exists(SPRAVOCHNIK_FILE):
        return []
    wb = load_workbook(SPRAVOCHNIK_FILE)
    ws = wb.active
    items = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if row[0]:
            date_val = row[4]
            if hasattr(date_val, 'strftime'):
                date_str = date_val.strftime('%d.%m.%Y')
            else:
                date_str = str(date_val) if date_val else ''
            items.append({
                'nomenclatura': row[0],
                'ed_izm': row[1],
                'cena': float(row[2]) if row[2] else 0,
                'valuta': row[3] or 'RUB',
                'data': date_str
            })
    return items


def load_vor():
    if not os.path.exists(VOR_FILE):
        return []
    wb = load_workbook(VOR_FILE)
    ws = wb.active
    items = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if row[0] is not None:
            items.append({
                'num': row[0],
                'naimenovanie': row[1],
                'ed_izm': row[2],
                'kolvo': float(row[3]) if row[3] else 0
            })
    return items


def load_mapping():
    if not os.path.exists(MAPPING_FILE):
        return {}
    with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_mapping(mapping):
    with open(MAPPING_FILE, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)


def save_spravochnik(items):
    wb = Workbook()
    ws = wb.active
    ws.append(['Номенклатура', 'Ед.изм', 'Цена', 'Валюта', 'Дата'])
    for item in items:
        ws.append([item['nomenclatura'], item['ed_izm'], item['cena'], item['valuta'], item['data']])
    wb.save(SPRAVOCHNIK_FILE)


# ─── Авторизация ───────────────────────────────────────────────────────────────

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        if username in USERS and USERS[username]['password'] == password:
            session['user'] = username
            session['role'] = USERS[username]['role']
            session['name'] = USERS[username]['name']
            return redirect(url_for('dashboard'))
        error = 'Неверный логин или пароль'
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ─── Дашборд ───────────────────────────────────────────────────────────────────

@app.route('/')
@login_required
def dashboard():
    return render_template('dashboard.html')


# ─── ВОР — Кладка ─────────────────────────────────────────────────────────────

@app.route('/tender/kholodov/kladka')
@login_required
def vor_kladka():
    vor_items = load_vor()
    spravochnik = load_spravochnik()
    mapping = load_mapping()

    result = []
    for item in vor_items:
        key = str(item['num'])
        mapped = mapping.get(key, {})
        material = mapped.get('material', '')
        cena = 0.0
        itogo = 0.0
        if material:
            for s in spravochnik:
                if s['nomenclatura'] == material:
                    cena = s['cena']
                    itogo = cena * item['kolvo']
                    break
        result.append({**item, 'material': material, 'cena': cena, 'itogo': itogo})

    total = sum(r['itogo'] for r in result)
    return render_template('vor.html', items=result, spravochnik=spravochnik, total=total)


@app.route('/vor/upload', methods=['POST'])
@login_required
def vor_upload():
    if 'file' in request.files:
        f = request.files['file']
        if f.filename:
            f.save(VOR_FILE)
    return redirect(url_for('vor_kladka'))


@app.route('/vor/mapping', methods=['POST'])
@login_required
def vor_mapping():
    data = request.json
    pos_num = str(data.get('num'))
    material = data.get('material', '')

    mapping = load_mapping()
    mapping[pos_num] = {'material': material}
    save_mapping(mapping)

    spravochnik = load_spravochnik()
    vor = load_vor()

    kolvo = 0.0
    for item in vor:
        if str(item['num']) == pos_num:
            kolvo = item['kolvo']
            break

    cena = 0.0
    for s in spravochnik:
        if s['nomenclatura'] == material:
            cena = s['cena']
            break

    itogo = cena * kolvo
    return jsonify({'success': True, 'cena': cena, 'itogo': itogo,
                    'cena_fmt': f'{cena:,.0f}'.replace(',', ' '),
                    'itogo_fmt': f'{itogo:,.0f}'.replace(',', ' ')})


# ─── Справочник цен ────────────────────────────────────────────────────────────

@app.route('/spravochnik')
@login_required
def spravochnik():
    items = load_spravochnik()
    return render_template('spravochnik.html', items=items)


@app.route('/spravochnik/upload', methods=['POST'])
@login_required
def spravochnik_upload():
    if 'file' in request.files:
        f = request.files['file']
        if f.filename:
            f.save(SPRAVOCHNIK_FILE)
    return redirect(url_for('spravochnik'))


@app.route('/spravochnik/update', methods=['POST'])
@login_required
def spravochnik_update():
    if session.get('role') != 'pricing':
        return jsonify({'error': 'Нет прав'}), 403
    data = request.json
    items = load_spravochnik()
    for item in items:
        if item['nomenclatura'] == data['nomenclatura']:
            item['cena'] = float(data['cena'])
            item['data'] = datetime.now().strftime('%d.%m.%Y')
            break
    save_spravochnik(items)
    return jsonify({'success': True, 'data': datetime.now().strftime('%d.%m.%Y')})


# ─── Экспорт Excel ─────────────────────────────────────────────────────────────

@app.route('/export')
@login_required
def export():
    vor_items = load_vor()
    spravochnik = load_spravochnik()
    mapping = load_mapping()

    wb = Workbook()
    ws = wb.active
    ws.title = 'Кладка — Расчёт'

    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    # Заголовок
    ws.merge_cells('A1:G1')
    ws['A1'] = f'ЖК Холодов | Раздел: Кладка | Расчёт от {datetime.now().strftime("%d.%m.%Y")}'
    ws['A1'].font = Font(bold=True, size=13, color='FFFFFF')
    ws['A1'].fill = PatternFill(fill_type='solid', fgColor='1a3a2a')
    ws['A1'].alignment = Alignment(horizontal='center')

    headers = ['№', 'Наименование', 'Ед.изм', 'Кол-во', 'Материал', 'Цена за ед., руб', 'Итого, руб']
    ws.append(headers)
    header_row = ws[2]
    for cell in header_row:
        cell.font = Font(bold=True, color='FFFFFF')
        cell.fill = PatternFill(fill_type='solid', fgColor='2d6a4f')
        cell.alignment = Alignment(horizontal='center')

    total = 0.0
    for item in vor_items:
        key = str(item['num'])
        material = mapping.get(key, {}).get('material', '')
        cena = 0.0
        itogo = 0.0
        if material:
            for s in spravochnik:
                if s['nomenclatura'] == material:
                    cena = s['cena']
                    itogo = cena * item['kolvo']
                    break
        total += itogo
        ws.append([item['num'], item['naimenovanie'], item['ed_izm'],
                   item['kolvo'], material, cena, itogo])

    # Итого
    total_row = ws.max_row + 1
    ws.cell(total_row, 6, 'ИТОГО:').font = Font(bold=True)
    ws.cell(total_row, 7, total).font = Font(bold=True)

    # Ширина столбцов
    widths = [5, 45, 8, 10, 25, 18, 15]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    filename = f'kladka_kholodov_{datetime.now().strftime("%d%m%Y")}.xlsx'
    return send_file(output, download_name=filename, as_attachment=True,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


if __name__ == '__main__':
    os.makedirs(DATA_DIR, exist_ok=True)
    app.run(debug=True, port=5000)
