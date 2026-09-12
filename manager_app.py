# __نظام إدارة الرواتب__
#استدعاء tkinter
import tkinter as tk
#استدعاء الرسائل من tkinter
from tkinter import messagebox, ttk
# استدعاء قواعد البيانات والتشفير 
import sqlite3, hashlib, csv
#استدعاء التاريخ والوقت
from datetime import datetime
# قاعدة البيانات
DB_PATH = 'payroll_system.db'
FONT    = "Arial"
#للاتصال بقواعد البيانات 
def get_connection(): return sqlite3.connect(DB_PATH)
# sha256 للتشفير باستخدام خوارزمية  
def hash_password(p: str) -> str:
    return hashlib.sha256(p.encode()).hexdigest()
#تعيين الجداول
def init_DB():
    conn = get_connection(); c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS employees (id TEXT PRIMARY KEY, name TEXT, original_salary REAL)")
    c.execute("CREATE TABLE IF NOT EXISTS admin_credentials (id INTEGER PRIMARY KEY, username TEXT, password_hash TEXT)")
    conn.commit(); conn.close()
# التشغيل الاولي للبرنامج 
def is_first_run() -> bool:
    conn = get_connection(); c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM admin_credentials")
    n = c.fetchone()[0]; conn.close(); return n == 0
# صنع المدير
def create_admin(u, p):
    conn = get_connection(); c = conn.cursor()
    c.execute("INSERT INTO admin_credentials (username,password_hash) VALUES(?,?)",(u,hash_password(p)))
    conn.commit(); conn.close()
#التحقق من المدير
def verify_admin(u, p) -> bool:
    conn = get_connection(); c = conn.cursor()
    c.execute("SELECT username,password_hash FROM admin_credentials WHERE id=1")
    row = c.fetchone(); conn.close()
    return bool(row and row[0]==u and row[1]==hash_password(p))
#السماح للبرنامج بوضع اسم المدير في شريط العنوان
def get_admin_username() -> str:
    conn = get_connection(); c = conn.cursor()
    c.execute("SELECT username FROM admin_credentials WHERE id=1")
    row = c.fetchone(); conn.close(); return row[0] if row else ""
#تعديل بيانات المدير
def update_admin_credentials(u, p):
    conn = get_connection(); c = conn.cursor()
    c.execute("UPDATE admin_credentials SET username=?,password_hash=? WHERE id=1",(u,hash_password(p)))
    conn.commit(); conn.close()
#__وظائف الموظفين__
#اضافة موظف 
def add_employee(eid, name, salary):
    conn = get_connection(); c = conn.cursor()
    c.execute("INSERT INTO employees VALUES(?,?,?)",(eid,name,float(salary)))
    conn.commit(); conn.close()
#استدعاء بيانات موظف
def get_employee(eid):
    conn = get_connection(); c = conn.cursor()
    c.execute("SELECT * FROM employees WHERE id=?",(eid,))
    row = c.fetchone(); conn.close(); return row
#استدعاء بيانات موظفين
def get_all_employees():
    conn = get_connection(); c = conn.cursor()
    c.execute("SELECT * FROM employees")
    rows = c.fetchall(); conn.close(); return rows
#حذف بيانات موظف
def delete_employee(eid):
    conn = get_connection(); c = conn.cursor()
    c.execute("DELETE FROM employees WHERE id=?",(eid,))
    conn.commit(); conn.close()
#حساب راتب الموظف
def calc_salary(base, hours=0, bonus=0, deductions=0) -> dict:
    if base <= 0:        raise ValueError("الراتب الأساسي يجب أن يكون أكبر من صفر")
    if hours < 0:        raise ValueError("ساعات العمل لا يمكن أن تكون سالبة")
    if bonus < 0:        raise ValueError("المكافآت لا يمكن أن تكون سالبة")
    if deductions < 0:   raise ValueError("الخصومات لا يمكن أن تكون سالبة")
    if hours > 720:      raise ValueError("عدد الساعات غير منطقي")
    if deductions>=base: raise ValueError("الخصومات لا يمكن أن تتجاوز الراتب الأساسي")
    overtime = round(hours * (base/176) * 1.5, 2)
    gross    = round(base + overtime + bonus, 2)
    tax      = round(gross * 0.05, 2)
    social   = round(base  * 0.03, 2)
    total_d  = round(tax + social + deductions, 2)
    return dict(base_salary=base, hours=hours, overtime_pay=overtime, bonus=bonus,
                gross=gross, tax=tax, social_ins=social,
                deductions=deductions, total_deduct=total_d, net=round(gross-total_d,2))
# مساعدات UI
_screen    = None
_sal_data: dict = {}
def clear_root():
    for w in root.winfo_children(): w.destroy()
def go(fn):
    global _screen; _screen = fn; fn()
def btn(parent, text, cmd, **kw):
    return tk.Button(parent, text=text, font=(FONT,11), cursor="hand2", command=cmd, **kw)
def entry(parent, show="", **kw):
    return tk.Entry(parent, font=(FONT,12), relief="solid", bd=1,
                    justify="center", show=show, **kw)
def lbl(parent, text, size=11, bold=False):
    f = (FONT, size, "bold") if bold else (FONT, size)
    return tk.Label(parent, text=text, font=f)
def header(parent, title, subtitle=""):
    f = tk.Frame(parent, pady=16, relief="groove", bd=2); f.pack(fill="x")
    tk.Label(f, text=title, font=(FONT,15,"bold")).pack()
    if subtitle:
        tk.Label(f, text=subtitle, font=(FONT,10)).pack()
    return f
def vd(): return (root.register(lambda P: P=="" or P.isdigit()), '%P')
def vn(): return (root.register(lambda P: P=="" or P.replace('.','',1).isdigit()), '%P')
# شاشة الإعداد الأولي
def build_setup():
    clear_root(); root.geometry("400x500"); root.title("إعداد النظام")
    frm = tk.Frame(root); frm.pack(fill="both", expand=True)
    header(frm, " إعداد النظام", "أنشئ حساب المدير — يظهر مرة واحدة فقط")
    inn = tk.Frame(frm, padx=40); inn.pack(fill="x", pady=20)
    lbl(inn,"اسم المستخدم:").pack(anchor="e", pady=(0,2))
    e_u = entry(inn); e_u.pack(fill="x", ipady=7)
    lbl(inn,"كلمة المرور:").pack(anchor="e", pady=(12,2))
    e_p = entry(inn, show="*"); e_p.pack(fill="x", ipady=7)
    sv = tk.StringVar()
    sl = tk.Label(inn, textvariable=sv, font=(FONT,9), anchor="e"); sl.pack(fill="x")
    def chk(*_):
        p=e_p.get()
        sc=sum([len(p)>=8,any(c.isupper()for c in p),any(c.isdigit()for c in p),any(c in"!@#$%"for c in p)])
        d={0:("",),1:("ضعيفة",),2:("متوسطة",),3:("جيدة",),4:("قوية",)}
        sv.set(d[sc][0])
    e_p.bind("<KeyRelease>", chk)
    lbl(inn,"تأكيد كلمة المرور:").pack(anchor="e", pady=(12,2))
    e_c = entry(inn, show="*"); e_c.pack(fill="x", ipady=7)
    def go_create():
        u,p,c = e_u.get().strip(),e_p.get().strip(),e_c.get().strip()
        if not u: messagebox.showwarning("!","اسم المستخدم مطلوب"); return
        if len(p)<6: messagebox.showwarning("!","كلمة المرور 6 أحرف على الأقل"); return
        if p!=c: messagebox.showerror("!","كلمتا المرور غير متطابقتين"); return
        create_admin(u,p); messagebox.showinfo("","تم إنشاء الحساب!"); go(build_login)
    btn(inn,"  إنشاء الحساب والبدء", go_create).pack(fill="x", pady=18, ipady=8)
# شاشة تسجيل الدخول
def build_login():
    clear_root(); root.geometry("380x360"); root.title("نظام إدارة الرواتب")
    frm = tk.Frame(root); frm.pack(fill="both", expand=True)
    header(frm, " نظام إدارة الرواتب", "بوابة المدير")
    inn = tk.Frame(frm, padx=40); inn.pack(fill="x", pady=24)
    lbl(inn,"اسم المستخدم:").pack(anchor="e", pady=(0,2))
    e_u = entry(inn); e_u.pack(fill="x", ipady=7)
    lbl(inn,"كلمة المرور:").pack(anchor="e", pady=(10,2))
    e_p = entry(inn, show="*"); e_p.pack(fill="x", ipady=7)
    def do_login():
        u,p = e_u.get().strip(), e_p.get().strip()
        if not u or not p: messagebox.showwarning("!","أدخل اسم المستخدم وكلمة المرور"); return
        if verify_admin(u,p): go(build_main)
        else:
            messagebox.showerror("!","بيانات الدخول غير صحيحة")
            e_p.delete(0, tk.END)
    e_p.bind("<Return>", lambda _: do_login())
    btn(inn,"  دخول", do_login).pack(fill="x", pady=18, ipady=8)
# اللوحة الرئيسية   
e_id=e_name=e_sal=e_del_id=None
e_cid=e_hrs=e_bon=e_ded=None
lbl_res=btn_slip=None
def build_main():
    global e_id,e_name,e_sal,e_del_id,e_cid,e_hrs,e_bon,e_ded,lbl_res,btn_slip
    clear_root(); root.geometry("480x700"); root.title("لوحة تحكم المدير")
    #  شريط أعلى 
    top = tk.Frame(root, pady=8, relief="groove", bd=2); top.pack(fill="x")
    tk.Label(top, text=" نظام إدارة الرواتب", font=(FONT,12,"bold")).pack(side="left", padx=12)
    tk.Label(top, text=f" {get_admin_username()}", font=(FONT,10)).pack(side="right", padx=12)
    #  منطقة قابلة للتمرير 
    canvas = tk.Canvas(root, highlightthickness=0)
    sb = ttk.Scrollbar(root, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=sb.set)
    sb.pack(side="right", fill="y")
    canvas.pack(fill="both", expand=True)
    body = tk.Frame(canvas)
    body_id = canvas.create_window((0,0), window=body, anchor="nw")
    def on_resize(e):
        canvas.itemconfig(body_id, width=e.width)
    def on_frame(e):
        canvas.configure(scrollregion=canvas.bbox("all"))
    canvas.bind("<Configure>", on_resize)
    body.bind("<Configure>", on_frame)
    canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(-1*(e.delta//120),"units"))
    pad = dict(padx=20, pady=6, fill="x")
    # قسم: الموظفون
    sec_title(body, " الموظفون")
    row1 = tk.Frame(body); row1.pack(**pad)
    # إضافة
    box_add = card(row1, "إضافة موظف"); box_add.pack(side="left", expand=True, fill="both", padx=(0,6))
    lbl(box_add,"الرقم الوظيفي (5-7 أرقام):",10).pack(anchor="e")
    e_id = entry(box_add, validate="key", validatecommand=vd()); e_id.pack(fill="x", ipady=5, pady=2)
    lbl(box_add,"اسم الموظف:",10).pack(anchor="e")
    e_name = entry(box_add); e_name.pack(fill="x", ipady=5, pady=2)
    lbl(box_add,"الراتب الأساسي:",10).pack(anchor="e")
    e_sal = entry(box_add, validate="key", validatecommand=vn()); e_sal.pack(fill="x", ipady=5, pady=2)
    btn(box_add,"  حفظ", save_employee).pack(fill="x", pady=8, ipady=5)
    # حذف
    box_del = card(row1, "حذف موظف"); box_del.pack(side="left", expand=True, fill="both", padx=(6,0))
    lbl(box_del,"رقم الموظف:",10).pack(anchor="e")
    e_del_id = entry(box_del, validate="key", validatecommand=vd()); e_del_id.pack(fill="x", ipady=5, pady=2)
    btn(box_del,"  حذف", delete_emp).pack(fill="x", pady=4, ipady=5)
    tk.Frame(box_del, height=4).pack()
    btn(box_del,"  عرض الكل", view_employees).pack(fill="x", ipady=4)
    tk.Frame(box_del, height=4).pack()
    btn(box_del,"  تصدير CSV", export_csv_emp).pack(fill="x", ipady=4)
    tk.Frame(body, height=1, relief="groove", bd=1).pack(fill="x", padx=20, pady=10)
    # قسم: الرواتب
    sec_title(body, "  حساب الراتب")
    box_sal = card(body, ""); box_sal.pack(**pad)
    lbl(box_sal,"رقم الموظف:",10).pack(anchor="e")
    e_cid = entry(box_sal, validate="key", validatecommand=vd()); e_cid.pack(fill="x", ipady=5, pady=2)
    row_lbl = tk.Frame(box_sal); row_lbl.pack(fill="x", pady=(8,0))
    row_inp = tk.Frame(box_sal); row_inp.pack(fill="x", pady=2)
    for t in ["ساعات إضافية","مكافآت","خصومات"]:
        tk.Label(row_lbl, text=t, font=(FONT,9), anchor="center").pack(side="left", expand=True)
    e_hrs = entry(row_inp, validate="key", validatecommand=vn(), width=8)
    e_bon = entry(row_inp, validate="key", validatecommand=vn(), width=8)
    e_ded = entry(row_inp, validate="key", validatecommand=vn(), width=8)
    for e in [e_hrs, e_bon, e_ded]: e.pack(side="left", expand=True, padx=3, ipady=5)
    br = tk.Frame(box_sal); br.pack(fill="x", pady=8)
    btn(br,"  احسب", calculate_salary).pack(side="left", expand=True, fill="x", padx=(0,4), ipady=6)
    btn_slip = btn(br,"  قسيمة", issue_slip)
    btn_slip.pack(side="left", expand=True, fill="x", padx=(4,0), ipady=6)
    btn_slip.config(state="disabled")
    lbl_res = tk.Label(box_sal, text="", font=(FONT,10),
                       justify="right", anchor="e", wraplength=400)
    lbl_res.pack(fill="x", pady=4)
    tk.Frame(body, height=1, relief="groove", bd=1).pack(fill="x", padx=20, pady=10)
    # قسم: الإعدادات
    sec_title(body, "  الإعدادات")
    box_cfg = card(body, "تغيير بيانات الدخول"); box_cfg.pack(**pad)
    lbl(box_cfg,"كلمة المرور الحالية:",10).pack(anchor="e")
    e_op = entry(box_cfg, show="*"); e_op.pack(fill="x", ipady=5, pady=2)
    lbl(box_cfg,"اسم المستخدم الجديد:",10).pack(anchor="e")
    e_nu = entry(box_cfg); e_nu.insert(0, get_admin_username()); e_nu.pack(fill="x", ipady=5, pady=2)
    lbl(box_cfg,"كلمة المرور الجديدة:",10).pack(anchor="e")
    e_np = entry(box_cfg, show="*"); e_np.pack(fill="x", ipady=5, pady=2)
    lbl(box_cfg,"تأكيد كلمة المرور:",10).pack(anchor="e")
    e_cp = entry(box_cfg, show="*"); e_cp.pack(fill="x", ipady=5, pady=2)
    def save_creds():
        if not verify_admin(get_admin_username(), e_op.get().strip()):
            messagebox.showerror("!","كلمة المرور الحالية غير صحيحة"); return
        u,p = e_nu.get().strip(), e_np.get().strip()
        if not u: messagebox.showwarning("!","اسم المستخدم مطلوب"); return
        if len(p)<6: messagebox.showwarning("!","كلمة المرور 6 أحرف على الأقل"); return
        if p!=e_cp.get().strip(): messagebox.showerror("!","كلمتا المرور غير متطابقتين"); return
        update_admin_credentials(u,p)
        messagebox.showinfo("",f"تم التحديث!\nاسم المستخدم: {u}")
    btn(box_cfg,"  حفظ التغييرات", save_creds).pack(fill="x", pady=8, ipady=6)
    btn(body,"  تسجيل الخروج", lambda: go(build_login)
        ).pack(padx=20, pady=12, fill="x", ipady=7)
# ── مكونات مساعدة ──
def sec_title(parent, text):
    tk.Label(parent, text=text, font=(FONT,12,"bold"),
             anchor="e").pack(fill="x", padx=20, pady=(10,4))

def card(parent, title):
    f = tk.Frame(parent, relief="solid", bd=1, padx=12, pady=10)
    if title:
        tk.Label(f, text=title, font=(FONT,10,"bold"),
                 anchor="e").pack(fill="x", pady=(0,6))
    return f
# وظائف الموظفين
# قيم الادخال
def validate_emp_id(v):
    if not v.isdigit(): return "الرقم الوظيفي يجب أن يحتوي على أرقام فقط"
    if not (5<=len(v)<=7): return "الرقم الوظيفي يجب أن يكون بين 5 و 7 أرقام"
    return None
def validate_name(v):
    if not v: return "الاسم لا يمكن أن يكون فارغاً"
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ "
                  "ءآأؤإئابتثجحخدذرزسشصضطظعغفقكلمنهوىيةًٌٍَُِّْ")
    if not all(c in allowed for c in v): return "الاسم يجب أن يحتوي على حروف ومسافات فقط"
    return None
def validate_salary(v):
    try:
        if float(v)<=0: raise ValueError
    except ValueError: return "الراتب يجب أن يكون رقماً موجباً"
    return None
#حفظ الموظف
def save_employee():
    eid,name,sal = e_id.get().strip(),e_name.get().strip(),e_sal.get().strip()
    for v,f in [(eid,validate_emp_id),(name,validate_name),(sal,validate_salary)]:
        err=f(v)
        if err: messagebox.showwarning("!",err); return
    try:
        add_employee(eid,name,float(sal))
        messagebox.showinfo("","تمت إضافة الموظف بنجاح!")
        for e in [e_id,e_name,e_sal]: e.delete(0,tk.END)
    except: messagebox.showerror("!","الرقم الوظيفي موجود مسبقاً")
# حذف الموظف
def delete_emp():
    eid = e_del_id.get().strip()
    if not eid: messagebox.showwarning("!","أدخل الرقم الوظيفي"); return
    if messagebox.askyesno("تأكيد",f"هل تريد حذف الموظف {eid}؟"):
        delete_employee(eid)
        messagebox.showinfo("","تم الحذف بنجاح")
        e_del_id.delete(0,tk.END)
# عرض الموظفين 
def view_employees():
    win=tk.Toplevel(root); win.title("سجل الموظفين"); win.geometry("500x300")
    tree=ttk.Treeview(win,columns=("ID","Name","Salary"),show="headings")
    tree.heading("ID",text="الرقم الوظيفي")
    tree.heading("Name",text="الاسم")
    tree.heading("Salary",text="الراتب الأساسي")
    tree.pack(fill="both",expand=True,padx=10,pady=10)
    for row in get_all_employees(): tree.insert("",tk.END,values=row)
# تصدير csv
def export_csv_emp():
    rows=get_all_employees()
    fn=f"employees_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    with open(fn,'w',newline='',encoding='utf-8-sig') as f:
        w=csv.writer(f)
        w.writerow(["الرقم الوظيفي","الاسم","الراتب الأساسي"])
        w.writerows(rows)
    messagebox.showinfo("",f"تم التصدير: {fn}")
# وظائف الرواتب
def calculate_salary():
    global _sal_data
    eid=e_cid.get().strip()
    if not eid: messagebox.showwarning("!","أدخل رقم الموظف"); return
    emp=get_employee(eid)
    if not emp:
        lbl_res.config(text=" الموظف غير موجود"); btn_slip.config(state="disabled"); return
    try:
        h=float(e_hrs.get() or 0); b=float(e_bon.get() or 0); d=float(e_ded.get() or 0)
        r=calc_salary(emp[2],h,b,d)
        _sal_data={**r,"id":emp[0],"name":emp[1],"date":datetime.now().strftime("%Y-%m-%d %H:%M")}
        lbl_res.config(
            text=(f"الموظف: {emp[1]}   |   الرقم: {emp[0]}\n"
                  f"الأساسي: {r['base_salary']:,.2f}   الإضافي: {r['overtime_pay']:,.2f}   المكافآت: {r['bonus']:,.2f}\n"
                  f"الإجمالي: {r['gross']:,.2f}   الضريبة: {r['tax']:,.2f}   التأمين: {r['social_ins']:,.2f}\n"
                  f"إجمالي الخصومات: {r['total_deduct']:,.2f}\n"
                  f"  صافي الراتب: {r['net']:,.2f} دينار"))
        btn_slip.config(state="normal")
    except ValueError as e: messagebox.showerror("!",str(e))
#اصدار قسيمة
def issue_slip():
    if not _sal_data: messagebox.showwarning("!","احسب الراتب أولاً"); return
    d=_sal_data
    win=tk.Toplevel(root); win.title("قسيمة الراتب")
    win.geometry("440x580"); win.resizable(False,False)
    tk.Frame(win,pady=14,relief="groove",bd=2).pack(fill="x")
    h=win.children[list(win.children)[-1]]
    tk.Label(h,text=" نظام إدارة الرواتب",font=(FONT,14,"bold")).pack()
    tk.Label(h,text="قسيمة الراتب الشهري",font=(FONT,10)).pack()
    inf=tk.Frame(win,padx=14,pady=10,relief="solid",bd=1); inf.pack(fill="x",padx=16,pady=10)
    for l,v in [("الرقم الوظيفي",d['id']),("اسم الموظف",d['name']),("تاريخ الإصدار",d['date'])]:
        r=tk.Frame(inf); r.pack(fill="x")
        tk.Label(r,text=v,font=(FONT,10),anchor="w").pack(side="left")
        tk.Label(r,text=l,font=(FONT,10,"bold"),anchor="e").pack(side="right")
    def sec(title,rows):
        tk.Label(win,text=title,font=(FONT,11,"bold")).pack(pady=(6,0))
        sf=tk.Frame(win,padx=12,pady=8,relief="solid",bd=1); sf.pack(fill="x",padx=16)
        for lb,val,bold in rows:
            rw=tk.Frame(sf); rw.pack(fill="x",pady=1)
            f=(FONT,10,"bold") if bold else (FONT,10)
            tk.Label(rw,text=f"{val:,.2f}",font=f,width=14,anchor="w").pack(side="left")
            tk.Label(rw,text=lb,font=f,anchor="e").pack(side="right")
    sec("المستحقات",[
        ("الراتب الأساسي",d['base_salary'],False),
        (f"أجر إضافي ({d['hours']:.0f} ساعة)",d['overtime_pay'],False),
        ("مكافآت",d['bonus'],False),
        ("الإجمالي",d['gross'],True),
    ])
    sec("الخصومات",[
        ("ضريبة الدخل 5%",d['tax'],False),
        ("تأمينات اجتماعية 3%",d['social_ins'],False),
        ("خصومات أخرى",d['deductions'],False),
        ("إجمالي الخصومات",d['total_deduct'],True),
    ])
    nf=tk.Frame(win,pady=12,relief="groove",bd=2); nf.pack(fill="x",padx=16,pady=8)
    tk.Label(nf,text="صافي الراتب",font=(FONT,11)).pack()
    tk.Label(nf,text=f"{d['net']:,.2f} دينار",font=(FONT,18,"bold")).pack()
    bf=tk.Frame(win); bf.pack(pady=6)
    btn(bf,"  حفظ CSV",lambda:save_slip_csv(d)).pack(side="left",padx=6,ipady=4,ipadx=8)
    btn(bf,"  إغلاق",win.destroy).pack(side="left",padx=6,ipady=4,ipadx=8)
def save_slip_csv(d):
    fn=f"slip_{d['id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    with open(fn,'w',newline='',encoding='utf-8-sig') as f:
        w=csv.writer(f); w.writerow(["بند","المبلغ"])
        for row in [
            ["الرقم الوظيفي",d['id']],["الاسم",d['name']],["التاريخ",d['date']],[],
            ["الراتب الأساسي",d['base_salary']],["أجر إضافي",d['overtime_pay']],
            ["مكافآت",d['bonus']],["الإجمالي",d['gross']],[],
            ["ضريبة 5%",d['tax']],["تأمينات 3%",d['social_ins']],
            ["خصومات أخرى",d['deductions']],["إجمالي الخصومات",d['total_deduct']],[],
            ["صافي الراتب",d['net']]
        ]: w.writerow(row)
    messagebox.showinfo("",f"تم الحفظ: {fn}")
# تشغيل
init_DB()
root = tk.Tk()
root.title("نظام إدارة الرواتب")
root.resizable(False, False)
go(build_setup if is_first_run() else build_login)
root.mainloop()