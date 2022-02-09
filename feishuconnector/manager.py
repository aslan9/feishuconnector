import requests
import json
import datetime

class DateEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj,datetime.datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        elif isinstance(obj,datetime.date):
            return obj.strftime("%Y-%m-%d")
        else:
            return json.JSONEncoder.default(self,obj)
        
class FeishuConnector:
    
    def __init__(self):
        self.app_id = None
        self.app_secret = None
        self.token = None

    def init(self, app_id: str, app_secret: str) -> None:
        self.app_id = app_id
        self.app_secret = app_secret
        self.token = self.get_tenant_access_token()

    def log(self, msg: str):
        print(f'[FeishuC] {msg}')

    # important functions
    def get_bitable_records(self, node_token, table_id):
        app_token = self.get_app_token(node_token)
        has_more = True
        total_num = None
        page_token = None
        records = []
        try_num = 0
        while has_more:
            d = self._get_bitable_records(app_token, table_id, page_token=page_token)
            try_num += 1
            has_more = d['has_more']
            records.extend(d['items'])
            total_num = d['total']
            page_token = d['page_token']
        item_num = len(records)
        self.log(f'records from {node_token} table {table_id} with {try_num} requests. ApiTotal={total_num}, RecordNum={item_num}')
        return records
    
    def insert_bitable_records(self, node_token, table_id, records):
        app_token = self.get_app_token(node_token)
        num_inserted = 0
        try_num = 0
        item_num = len(records)
        while num_inserted < item_num:
            end = min(item_num, num_inserted + 100)
            rs = records[num_inserted: end]
            self._insert_bitable_record(app_token, table_id, rs)
            num_inserted = end
            try_num += 1
        self.log(f'records to {node_token} table {table_id} with {try_num} requests. ItemNum={num_inserted}, RecordNum={item_num}')
        return num_inserted
    
    def get_sheet_data(self, node_token, sheet_id):
        app_token = self.get_app_token(node_token)
        values = self._get_sheet_data(app_token, sheet_id)
        sz = len(values)
        self.log(f'data from {node_token} sheet {sheet_id} with {sz} rows')
        return values
    
    def append_sheet_data(self, node_token, sheet_id, values):
        app_token = self.get_app_token(node_token)
        sz = len(values)
        row_inserted = 0
        try_num = 0
        while row_inserted < sz:
            end = min(sz, row_inserted + 5000)
            rs = values[row_inserted: end]
            self._append_sheet_data(app_token, sheet_id, rs)
            row_inserted = end
            try_num += 1
        self.log(f'data to {node_token} table {sheet_id} with {try_num} requests. RowNum={row_inserted}, RecordNum={sz}')
        return row_inserted
    
    # utility funcs
    def get_tenant_access_token(self):
        payload = {'app_id': self.app_id, 'app_secret': self.app_secret}
        r = requests.post('https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal', data=payload)
        d = json.loads(r.text)
        assert d.get('code') == 0, f'fail to create tenant access token rsp={r.text}'
        token = d['tenant_access_token']
        self.log(f'access token fetched: {token}')
        return token

    def get_wiki_spaces(self):
        headers = {'Authorization': f'Bearer {self.token}'}
        r = requests.get(f'https://open.feishu.cn/open-apis/wiki/v2/spaces', params={}, headers=headers)
        d = json.loads(r.text)
        assert d.get('code') == 0, f'fail to get_wiki_spaces={r.text}'
        return d['data']['items']
    
    def get_nodes(self, space_id):
        headers = {'Authorization': f'Bearer {self.token}'}
        r = requests.get(f'https://open.feishu.cn/open-apis/wiki/v2/spaces/{space_id}/nodes', params={}, headers=headers)
        d = json.loads(r.text)
        assert d.get('code') == 0, f'fail to get_nodes={r.text}'
        nodes = d['data']['items']
        return nodes
    
    def get_node_detail(self, node_token):
        headers = {'Authorization': f'Bearer {self.token}'}
        r = requests.get(f'https://open.feishu.cn/open-apis/wiki/v2/spaces/get_node', params={'token': node_token}, headers=headers)
        d = json.loads(r.text)
        assert d.get('code') == 0, f'fail to get_node_detail={r.text}'
        detail = d['data']['node']
        return detail

    def get_app_token(self, node_token):
        detail = self.get_node_detail(node_token)
        app_token = detail['obj_token']
        return app_token
    
    
    # sheet funcs
    def get_sheet_meta(self, sheet_token):
        headers = {'Authorization': f'Bearer {self.token}'}
        r = requests.get(f'https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{sheet_token}/metainfo', params={}, headers=headers)
        d = json.loads(r.text)
        assert d.get('code') == 0, f'fail to get_sheet_meta={r.text}'
        return d['data']
    
    def _append_sheet_data(self, sheet_token, sheet_range, values):
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json; charset=utf-8'
        }
        d = {
            'valueRange': {
                'range': sheet_range,
                'values': values
            }
        }
        dt = json.dumps(d, cls=DateEncoder)
        req = requests.post(f'https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{sheet_token}/values_append', data=dt, headers=headers)
        res = json.loads(req.text)
        assert res.get('code') == 0, f'fail to _append_sheet_data={req.text}'
        cell_num = res['data']['updates']['updatedCells']
        row_num = res['data']['updates']['updatedRows']
        self.log(f'_append_sheet_data, res={req.text}')
        self.log(f'sheet data appended. (sheet_range){sheet_range} (cells){cell_num} (rows){row_num}')
        #assert d.get('code') == 0, f'fail to get_sheet_meta={r.text}'
        return res
    
    def _get_sheet_data(self, sheet_token, sheet_range):
        headers = {'Authorization': f'Bearer {self.token}'}
        r = requests.get(f'https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{sheet_token}/values/{sheet_range}', params={}, headers=headers)
        d = json.loads(r.text)
        assert d.get('code') == 0, f'fail to _get_sheet_data={d.text}'
        values = d['data']['valueRange']['values']
        sz = len(values)
        self.log(f'sheet data fetched. (sheet_range){sheet_range} (rows){sz}')
        return values

    # ---- bitable ----
    def get_bitable_detail(self, app_token):
        headers = {'Authorization': f'Bearer {self.token}'}
        r = requests.get(f'https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}', params={}, headers=headers)
        d = json.loads(r.text)
        assert d.get('code') == 0, f'fail to get_bitable_detail={r.text}'
        return d['data']['app']

    def get_bitable_tables(self, app_token):
        headers = {'Authorization': f'Bearer {self.token}'}
        r = requests.get(f'https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/', params={}, headers=headers)
        d = json.loads(r.text)
        assert d.get('code') == 0, f'fail to get_bitable_tables={r.text}'
        return d['data']['items']

    def get_bitable_views(self, app_token, table_id):
        headers = {'Authorization': f'Bearer {self.token}'}
        r = requests.get(f'https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/views', params={}, headers=headers)
        d = json.loads(r.text)
        assert d.get('code') == 0, f'fail to get_bitable_views={r.text}'
        return d['data']['items']

    def _get_bitable_records(self, app_token, table_id, page_token=None):
        headers = {'Authorization': f'Bearer {self.token}'}
        params = {
            'page_size': 100,
            'page_token': page_token
        }
        r = requests.get(f'https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records', params=params, headers=headers)
        d = json.loads(r.text)
        assert d.get('code') == 0, f'fail to get_bitable_records={r.text}'
        data = d['data']
        sz = len(data['items'])
        total_num = data['total']
        page_token = data['page_token']
        self.log(f'bitable records fetched. (table_id){table_id} (num){sz} (page_t){page_token} (total){total_num}')
        return data

    def _insert_bitable_record(self, app_token, table_id, records):
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json; charset=utf-8'
        }
        ds = []
        for r in records:
            ds.append({'fields': r})
        dt = json.dumps({'records':ds})
        r = requests.post(f'https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create', data=dt, headers=headers)
        d = json.loads(r.text)
        sz = len(records)
        assert d.get('code') == 0, f'fail to _insert_bitable_record={r.text}'
        self.log(f'bitable records inserted. (table_id){table_id} (num){sz}')
        return d['data']['records']