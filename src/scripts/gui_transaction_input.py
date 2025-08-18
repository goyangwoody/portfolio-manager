import sys
import os
# Ensure the project's `src` directory is on sys.path so `import pm...` works
# when running the script from the repository root (e.g. `python src/scripts/gui_transaction_input.py`).
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if src_path not in sys.path:
    # insert at front so local packages shadow installed ones if any
    sys.path.insert(0, src_path)

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

from pm.db.models import SessionLocal, Portfolio, Asset, Transaction
from pm.portfolio.insert_transaction import add_transaction

# === Decimal helpers (Numeric(20,8) 정밀도에 맞춤) ===
SCALE = Decimal("0.00000001")  # 8자리 소수

def _to_decimal_or_zero(s: str) -> Decimal:
    s = (s or "").strip().replace(",", "")
    if s == "":
        return Decimal("0")
    try:
        return Decimal(s).quantize(SCALE, rounding=ROUND_HALF_UP)
    except InvalidOperation:
        raise ValueError(f"숫자 형식이 아닙니다: '{s}'")

def _fmt_decimal(x) -> str:
    """Treeview 표시용 문자열 포맷. None 방지 및 불필요한 0 제거."""
    if x is None:
        return "0"
    try:
        d = Decimal(x).quantize(SCALE, rounding=ROUND_HALF_UP)
    except Exception:
        return str(x)
    s = format(d.normalize(), 'f')
    if '.' in s:
        s = s.rstrip('0').rstrip('.')
        if s == '':
            s = '0'
    return s

# DB에서 포트폴리오와 자산 리스트 로드
session = SessionLocal()
portfolios = session.query(Portfolio).all()
assets = session.query(Asset).all()
session.close()

# 전역 리스트
portfolio_names = [p.name for p in portfolios]
asset_names = [a.name for a in assets]

class TransactionInputApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Transaction Manager')
        self.geometry('980x700')
        self.create_widgets()
        self.populate_transactions()  # 초기 로드

    def create_widgets(self):
        # ===== 상단: 표시용 포트폴리오 필터 =====
        filter_frame = ttk.LabelFrame(self, text='표시 필터')
        filter_frame.pack(fill='x', padx=10, pady=(10, 0))

        ttk.Label(filter_frame, text='표시할 포트폴리오:').grid(row=0, column=0, padx=5, pady=8, sticky='e')
        self.view_portfolio_var = tk.StringVar(value='전체')
        self.view_portfolio_cb = ttk.Combobox(
            filter_frame,
            textvariable=self.view_portfolio_var,
            values=['전체'] + portfolio_names,
            state='readonly',
            width=24
        )
        self.view_portfolio_cb.grid(row=0, column=1, padx=5, pady=8, sticky='w')
        self.view_portfolio_cb.bind('<<ComboboxSelected>>', self.on_view_portfolio_change)

        ttk.Button(filter_frame, text='새로고침', command=self.populate_transactions).grid(row=0, column=2, padx=10, pady=8)

        # ===== 거래 입력 프레임 =====
        input_frame = ttk.LabelFrame(self, text='거래 입력')
        input_frame.pack(fill='x', padx=10, pady=10)

        # Portfolio (입력용)
        ttk.Label(input_frame, text='포트폴리오:').grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.portfolio_var = tk.StringVar()
        self.portfolio_cb = ttk.Combobox(input_frame, textvariable=self.portfolio_var, values=portfolio_names, state='readonly')
        self.portfolio_cb.grid(row=0, column=1, padx=5, pady=5)

        # Asset Search
        ttk.Label(input_frame, text='자산 검색:').grid(row=0, column=2, padx=5, pady=5, sticky='e')
        self.asset_search_var = tk.StringVar()
        self.asset_search_entry = ttk.Entry(input_frame, textvariable=self.asset_search_var)
        self.asset_search_entry.grid(row=0, column=3, padx=5, pady=5)
        self.asset_search_var.trace('w', self.filter_assets)

        # Asset Combo
        ttk.Label(input_frame, text='자산:').grid(row=1, column=0, padx=5, pady=5, sticky='e')
        self.asset_var = tk.StringVar()
        self.asset_cb = ttk.Combobox(input_frame, textvariable=self.asset_var, values=asset_names, state='readonly')
        self.asset_cb.grid(row=1, column=1, padx=5, pady=5)

        # Transaction Date
        ttk.Label(input_frame, text='거래일자:').grid(row=1, column=2, padx=5, pady=5, sticky='e')
        self.date_var = tk.StringVar(value=datetime.today().strftime('%Y-%m-%d'))
        self.date_entry = ttk.Entry(input_frame, textvariable=self.date_var)
        self.date_entry.grid(row=1, column=3, padx=5, pady=5)

        # Quantity
        ttk.Label(input_frame, text='수량:').grid(row=2, column=0, padx=5, pady=5, sticky='e')
        self.qty_var = tk.StringVar()
        self.qty_entry = ttk.Entry(input_frame, textvariable=self.qty_var)
        self.qty_entry.grid(row=2, column=1, padx=5, pady=5)

        # Price
        ttk.Label(input_frame, text='단가:').grid(row=2, column=2, padx=5, pady=5, sticky='e')
        self.price_var = tk.StringVar()
        self.price_entry = ttk.Entry(input_frame, textvariable=self.price_var)
        self.price_entry.grid(row=2, column=3, padx=5, pady=5)

        # Fee, Tax
        ttk.Label(input_frame, text='수수료(fee):').grid(row=3, column=0, padx=5, pady=5, sticky='e')
        self.fee_var = tk.StringVar()
        self.fee_entry = ttk.Entry(input_frame, textvariable=self.fee_var)
        self.fee_entry.grid(row=3, column=1, padx=5, pady=5)

        ttk.Label(input_frame, text='세금(tax):').grid(row=3, column=2, padx=5, pady=5, sticky='e')
        self.tax_var = tk.StringVar()
        self.tax_entry = ttk.Entry(input_frame, textvariable=self.tax_var)
        self.tax_entry.grid(row=3, column=3, padx=5, pady=5)

        # Type
        ttk.Label(input_frame, text='거래 유형:').grid(row=4, column=0, padx=5, pady=5, sticky='e')
        self.type_var = tk.StringVar()
        self.type_cb = ttk.Combobox(input_frame, textvariable=self.type_var, values=['BUY', 'SELL', 'DEPOSIT', 'WITHDRAW', 'DIVIDEND'], state='readonly')
        self.type_cb.grid(row=4, column=1, padx=5, pady=5)

        # Buttons
        ttk.Button(input_frame, text='입력', command=self.on_submit).grid(row=4, column=2, padx=5, pady=10)
        ttk.Button(input_frame, text='취소', command=self.clear_fields).grid(row=4, column=3, padx=5, pady=10)

        # ===== 거래 기록 프레임 =====
        record_frame = ttk.LabelFrame(self, text='거래 기록')
        record_frame.pack(fill='both', expand=True, padx=10, pady=10)

        columns = ('id', 'portfolio', 'asset', 'date', 'quantity', 'price', 'fee', 'tax', 'type')
        self.tree = ttk.Treeview(record_frame, columns=columns, show='headings')
        for col in columns:
            if   col == 'id':         header = 'ID'
            elif col == 'portfolio':  header = '포트폴리오'
            elif col == 'asset':      header = '자산명'
            elif col == 'date':       header = '거래일자'
            elif col == 'quantity':   header = '수량'
            elif col == 'price':      header = '단가'
            elif col == 'fee':        header = '수수료'
            elif col == 'tax':        header = '세금'
            elif col == 'type':       header = '거래유형'
            else:                     header = col
            self.tree.heading(col, text=header)

            # 가독성: 금액/수량은 오른쪽 정렬
            anchor = 'e' if col in ('quantity', 'price', 'fee', 'tax') else 'center'
            width = 120
            if col in ('asset', 'portfolio'):
                width = 160
            if col == 'id':
                width = 60
            self.tree.column(col, anchor=anchor, width=width)

        self.tree.pack(fill='both', expand=True, side='left')

        scrollbar = ttk.Scrollbar(record_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side='right', fill='y')

        ttk.Button(self, text='선택 거래 삭제', command=self.on_delete).pack(pady=5)

    # === 표시 포트폴리오 변경 시 ===
    def on_view_portfolio_change(self, event=None):
        self.populate_transactions()

    def filter_assets(self, *args):
        query = self.asset_search_var.get().strip().upper()
        if query:
            filtered = [a.name for a in assets
                        if (a.ticker and query in a.ticker.upper()) or (a.name and query in a.name.upper())]
        else:
            filtered = [a.name for a in assets]
        self.asset_cb['values'] = filtered

    def populate_transactions(self):
        # Tree 초기화
        for row in self.tree.get_children():
            self.tree.delete(row)

        # 현재 표시 필터 확인
        view_name = self.view_portfolio_var.get().strip()
        selected_port_id = None
        if view_name and view_name != '전체':
            p = next((p for p in portfolios if p.name == view_name), None)
            selected_port_id = p.id if p else None

        # DB 로드 (필터 적용)
        session = SessionLocal()
        try:
            q = session.query(Transaction).order_by(Transaction.trans_date.desc())
            if selected_port_id is not None:
                q = q.filter(Transaction.portfolio_id == selected_port_id)
            txs = q.all()

            for tx in txs:
                self.tree.insert('', 'end', values=(
                    tx.id,
                    tx.portfolio.name if tx.portfolio else '',
                    tx.asset.name if tx.asset else '',
                    tx.trans_date.strftime('%Y-%m-%d'),
                    _fmt_decimal(tx.quantity),
                    _fmt_decimal(tx.price),
                    _fmt_decimal(getattr(tx, 'fee', Decimal("0"))),
                    _fmt_decimal(getattr(tx, 'tax', Decimal("0"))),
                    tx.type
                ))
        finally:
            session.close()

    def on_submit(self):
        try:
            # 필수값 체크
            if not self.portfolio_var.get():
                raise ValueError("포트폴리오를 선택하세요.")
            if not self.asset_var.get():
                raise ValueError("자산을 선택하세요.")
            if not self.type_var.get():
                raise ValueError("거래 유형을 선택하세요.")

            port_obj = next(p for p in portfolios if p.name == self.portfolio_var.get())
            asset_name = self.asset_var.get()
            asset_obj = next(a for a in assets if a.name == asset_name)

            # 날짜/숫자 파싱 (Decimal 정규화)
            trans_date = datetime.strptime(self.date_var.get(), '%Y-%m-%d').date()
            quantity   = _to_decimal_or_zero(self.qty_var.get())
            price      = _to_decimal_or_zero(self.price_var.get())
            fee        = _to_decimal_or_zero(self.fee_var.get())
            tax        = _to_decimal_or_zero(self.tax_var.get())
            ttype      = self.type_var.get()

            # add_transaction 호출
            add_transaction(
                portfolio_id=port_obj.id,
                asset_id=asset_obj.id,
                trans_date=trans_date,
                quantity=quantity,
                price=price,
                fee=fee,
                tax=tax,
                type_=ttype
            )
            messagebox.showinfo('성공', '거래가 정상 입력되었습니다.')
            self.populate_transactions()
        except Exception as e:
            messagebox.showerror('입력 오류', str(e))
            self.populate_transactions()

    def on_delete(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning('경고', '삭제할 거래를 선택하세요.')
            return
        confirm = messagebox.askyesno('삭제 확인', '선택한 거래를 정말 삭제하시겠습니까?')
        if not confirm:
            return
        tx_id = int(self.tree.item(selected[0], 'values')[0])
        session = SessionLocal()
        try:
            tx = session.query(Transaction).get(tx_id)
            session.delete(tx)
            session.commit()
            messagebox.showinfo('삭제 완료', f'거래 ID {tx_id}가 삭제되었습니다.')
            self.populate_transactions()
        except Exception as e:
            session.rollback()
            messagebox.showerror('삭제 오류', str(e))
        finally:
            session.close()

    def clear_fields(self):
        # 입력용 콤보/필드만 초기화 (보기 필터는 유지)
        self.portfolio_cb.set('')
        self.asset_search_var.set('')
        self.asset_cb.set('')
        self.date_var.set(datetime.today().strftime('%Y-%m-%d'))
        self.qty_var.set('')
        self.price_var.set('')
        self.fee_var.set('')
        self.tax_var.set('')
        self.type_var.set('')

if __name__ == '__main__':
    app = TransactionInputApp()
    app.mainloop()
