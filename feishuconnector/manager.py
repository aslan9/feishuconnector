
import uuid
import requests
import json
import tempfile
from .encoder import JsonEncoder
from typing import BinaryIO, Dict

import pandas as pd
import dataframe_image as dfi
from requests_toolbelt import MultipartEncoder


def create_unique_record_id(prefix='rec'):
    """Generate a unique record id for Feishu Bitable randomly."""
    
    return prefix + uuid.uuid4().hex[:10]

class FeishuConnector:

    def __init__(self, webhooks: Dict[str, str]):
        self.app_id = None
        self.app_secret = None
        self.token = None
        self._webhooks = webhooks
        assert self._webhooks is not None, 'you should put a webhook config here'
        assert 'default' in self._webhooks, 'you should put a test webhook here with key \"default\"'

    def init(self, app_id: str, app_secret: str) -> None:
        self.app_id = app_id
        self.app_secret = app_secret
        self.token = self.get_tenant_access_token()

    def log(self, msg: str):
        print(f'[FeishuC] {msg}')

    # important functions
    def get_bitable_records(self, node_token, table_id):
        d = self.get_node_detail(node_token)
        app_token = d['obj_token']
        obj_type = d['obj_type']
        if obj_type == 'sheet':
            # app token should be refactored
            sheet_meta = self.get_sheet_meta(app_token)
            for sht_info in sheet_meta['sheets']:
                if 'blockInfo' in sht_info:
                    token = sht_info['blockInfo']['blockToken']
                    _app, _table = token.split('_')
                    if _table == table_id:
                        app_token = _app
                        break
            self.log(f'[bitable] get from sheet: (node){node_token} (bi){app_token} (table){table_id}')
        elif obj_type == 'bitable':
            # just do nothing
            self.log(f'[bitable] get from sheet: (node){node_token} (bi){app_token} (table){table_id}')
        else:
            assert False, f'fail to get a correct node detail {d}'
        has_more = True
        total_num = None
        page_token = None
        records = []
        try_num = 0
        while has_more:
            if (page_token is None) and (try_num > 0):
                raise Exception('page_token is None while has more records to fetch.')
            d = self._get_bitable_records(app_token, table_id, page_token=page_token)
            try_num += 1
            has_more = d['has_more']
            total_num = d['total']
            if total_num != 0:
                records.extend(d['items'])
            page_token = d.get('page_token', None)
        item_num = len(records)
        self.log(f'records from {node_token} table {table_id} with {try_num} requests. ApiTotal={total_num}, RecordNum={item_num}')
        return records

    def insert_bitable_records(self, node_token, table_id, records):
        # to depreciated...
        self.log('insert_bitable_records will be replaced by append_bitable_records')
        return self.append_bitable_records(node_token, table_id, records)

    def append_bitable_records(self, node_token, table_id, records):
        d = self.get_node_detail(node_token)
        app_token = d['obj_token']
        obj_type = d['obj_type']
        if obj_type == 'sheet':
            # app token should be refactored
            sheet_meta = self.get_sheet_meta(app_token)
            for sht_info in sheet_meta['sheets']:
                if 'blockInfo' in sht_info:
                    token = sht_info['blockInfo']['blockToken']
                    _app, _table = token.split('_')
                    if _table == table_id:
                        app_token = _app
                        break
            self.log(f'[bitable] get from sheet: (node){node_token} (bi){app_token} (table){table_id}')
        elif obj_type == 'bitable':
            # just do nothing
            self.log(f'[bitable] get from sheet: (node){node_token} (bi){app_token} (table){table_id}')
        else:
            assert False, f'fail to get a correct node detail {d}'
        num_inserted = 0
        try_num = 0
        item_num = len(records)
        while num_inserted < item_num:
            end = min(item_num, num_inserted + 100)
            rs = records[num_inserted: end]
            self._append_bitable_record(app_token, table_id, rs)
            num_inserted = end
            try_num += 1
        self.log(f'records to {node_token} table {table_id} with {try_num} requests. ItemNum={num_inserted}, RecordNum={item_num}')
        return num_inserted
    
    def append_bitable_df(self, node_token, table_id, df: pd.DataFrame):
        d = self.get_node_detail(node_token)
        app_token = d['obj_token']
        self.log(f'[bitable] get from sheet: (node){node_token} (bi){app_token} (table){table_id}')
        self._append_bitable_df(app_token, table_id, df)
        self.log(f'data to {node_token} table {table_id} with 1 request. RecordNum={len(df)}')

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
        dt = json.dumps(d, cls=JsonEncoder)
        req = requests.post(f'https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{sheet_token}/values_append', data=dt, headers=headers)
        res = json.loads(req.text)
        assert res.get('code') == 0, f'fail to _append_sheet_data={req.text}'
        cell_num = res['data']['updates']['updatedCells']
        row_num = res['data']['updates']['updatedRows']
        self.log(f'_append_sheet_data, res={req.text}')
        self.log(f'sheet data appended. (sheet_range){sheet_range} (cells){cell_num} (rows){row_num}')
        # assert d.get('code') == 0, f'fail to get_sheet_meta={r.text}'
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
        total_num = data['total']
        # total为0时data中没有item字段
        if total_num == 0:
            sz = 0
        else:
            sz = len(data['items'])
        page_token = data.get('page_token', None)
        self.log(f'bitable records fetched. (table_id){table_id} (num){sz} (page_t){page_token} (total){total_num}')
        return data

    def _append_bitable_record(self, app_token, table_id, records):
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json; charset=utf-8'
        }
        ds = []
        for r in records:
            ds.append({'fields': r})
        dt = json.dumps({'records': ds})
        r = requests.post(f'https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create', data=dt, headers=headers)
        d = json.loads(r.text)
        sz = len(records)
        assert d.get('code') == 0, f'fail to _append_bitable_record={r.text}'
        self.log(f'bitable records inserted. (table_id){table_id} (num){sz}')
        return d['data']['records']
    
    def _append_bitable_df(self, app_token, table_id, df: pd.DataFrame):
        
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json; charset=utf-8'
        }
        
        # Convert timestamp data to int
        timestamp_columns = df.select_dtypes(include='datetime').columns
        for col in timestamp_columns:
            df[col] = (df[col].astype(int) / 10**6).astype(int)
        self.log(f'Timestamp columns: {timestamp_columns.tolist()}, converted to int')
        
        # Convert dataframe to format required by Feishu API
        records = []
        for _, row in df.iterrows():
            records.append({
                'record_id': create_unique_record_id(),
                'fields': row.to_dict(),
            })
            
        dt = json.dumps({'records': records}, indent=4)
        r = requests.post(f'https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create', data=dt, headers=headers)
        d = json.loads(r.text)
        sz = len(records)
        assert d.get('code') == 0, f'fail to _append_bitable_df={r.text}'
        self.log(f'bitable records inserted. (table_id){table_id} (num){sz}')
        return d['data']['records']

    def upload_images(self, image_binary: BinaryIO) -> str:
        import json

        form = {'image_type': 'message',
                'image': (image_binary)}
        multi_form = MultipartEncoder(form)
        self.log(f'(multi_form){multi_form}')
        headers = {
            'Authorization': f'Bearer {self.token}',
        }
        headers['Content-Type'] = multi_form.content_type
        rsp = requests.post('https://open.feishu.cn/open-apis/im/v1/images', headers=headers, data=multi_form)
        self.log(rsp.headers['X-Tt-Logid'])  # for debug or oncall
        d = json.loads(rsp.text)
        assert d.get('code') == 0, f'fail to upload image rsp={rsp.text}'
        image_key = d['data']['image_key']
        self.log(f'access token fetched: {image_key}')
        return image_key

    def send_image(self, fp, title, target=None):
        image_key = self.upload_images(fp)
        elements = [{
            "tag": "img",
            "title": {
                "tag": "plain_text",
                "content": title,
            },
            "img_key": image_key,
            "mode": "fit_horizontal",
            "alt": {
                "tag": "plain_text",
                "content": "",
            },
            "compact_width": True,
        }]
        self.send_webhook_msg(target=target, title=title, elements=elements)

    def send_dataframe(self, df: pd.DataFrame, title: str, target=None):
        try:
            with tempfile.TemporaryFile() as fp:
                dfi.export(df, fp, table_conversion='matplotlib')
                fp.seek(0)
                self.send_image(fp, title, target)
        except Exception as e:
            self.log(e)

    def send_webhook_msg(self, target=None, title=None, content=None, success=True, buttons=None, elements=None):
        '''
        buttons = [(content, url), (content, url)]
        '''
        msg = {
                "msg_type": "interactive",
                "card": {
                    "config": {
                        "wide_screen_mode": True
                    },
                    "elements": [{
                        "tag": "div",
                        "text":  {
                            "content": content or '',
                            "tag": "lark_md"
                        }
                    }] if elements is None else elements,
                    "header": {
                        "template": "green" if success else "red",
                        "title": {
                            "content": title or '',
                            "tag": "plain_text"
                        }
                    }
                }
            }
        if buttons:
            actions = []
            for (_c, _u) in buttons:
                actions.append({
                    "tag": "button",
                    "text": {
                        "content": _c,
                        "tag": "plain_text"
                    },
                    "type": "primary",
                    "url": _u
                })
            msg['card']['elements'].append({
                "actions": actions,
                "tag": "action"
            })
        try:
            url = self._webhooks[target] if target is not None else self._webhooks['default']
        except KeyError:
            url = ''
        if url:
            rsp = requests.post(
                url=url, json=msg, headers={
                    "Content-Type": "application/json"
                })
            self.log(rsp.text)
        else:
            self.log('cannot find proper webhook')

    def get_filtered_records(self, node_token, table_id, filter_conditions):
        """
        根据给定的条件筛选飞书多维表格中的记录。

        :param node_token: 飞书多维表格的节点令牌
        :param table_id: 飞书多维表格的ID
        :param filter_conditions: 筛选条件，字典格式，字段名作为键，期望值作为值
        :return: 符合条件的记录列表
        """
        all_records = self.get_bitable_records(node_token, table_id)
        filtered_records = [record for record in all_records if
                            all(record['fields'].get(key) == value for key, value in filter_conditions.items())]
        # print('filtered_records:',filtered_records)
        return filtered_records

    def update_bitable_record(self, node_token, table_id, filter_conditions, update_field, new_value):
        """
        更新飞书多维表格中符合条件的记录的指定字段(更新某一字段)。

        :param update_field: 要更新的字段名
        :param new_value: 新的字段值
        """
        return self.update_bitable_records(node_token, table_id, filter_conditions, {update_field: new_value})

    def update_bitable_records(self, node_token, table_id, filter_conditions, update_fields):
        """
        更新飞书多维表格中符合条件的记录的指定字段（更新多字段）。

        :param node_token: 飞书多维表格的节点令牌
        :param table_id: 飞书多维表格的ID
        :param filter_conditions: 筛选条件，字典格式，字段名作为键，期望值作为值
        :param update_fields: 字典格式：{‘更新的字段名1’：‘新的字段值1’，‘更新的字段名2’：‘新的字段值2’}
        """
        # 获取节点详情以确定使用的app_token
        d = self.get_node_detail(node_token)
        app_token = d['obj_token']
        # 获取符合条件的记录
        records = self.get_filtered_records(node_token, table_id, filter_conditions)
        updated_num = 0
        for record in records:
            # 构建更新后的记录
            updated_record = {
                'record_id': record['record_id'],  # 需要指定记录ID
                'fields': {
                    **record['fields'],  # 保留原有字段
                    **update_fields  # 更新指定字段
                }
            }
            updated_count = 0
            # 调用API更新记录
            headers = {
                'Authorization': f'Bearer {self.token}',
                'Content-Type': 'application/json; charset=utf-8'
            }
            record_id = record['record_id']
            # print('record:',record)

            url = f'https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}'
            response = requests.put(url, headers=headers, json=updated_record)
            # print('response:',response.json())
            # 检查API调用是否成功
            if response.status_code == 200:
                # print('api调用成功')
                updated_count += 1
            else:
                # print('api调用失败')
                self.log(f'Failed to update record {record["record_id"]}: {response.text}')
        # 返回更新的记录数量
        return updated_num
