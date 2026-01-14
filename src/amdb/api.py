"""
RESTful API 和 GraphQL API
提供外部访问接口
"""

from typing import Dict, Any, Optional, List
try:
    from flask import Flask, request, jsonify
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    Flask = None
    request = None
    jsonify = None

from .database import Database
from .query import QueryEngine


class RESTAPI:
    """RESTful API服务器"""
    
    def __init__(self, db: Database, host: str = "0.0.0.0", port: int = 8080):
        if not FLASK_AVAILABLE:
            raise ImportError("Flask is required for REST API. Install it with: pip install flask")
        self.db = db
        self.query_engine = QueryEngine(db)
        self.app = Flask(__name__)
        self.host = host
        self.port = port
        self._setup_routes()
    
    def _setup_routes(self):
        """设置路由"""
        
        @self.app.route('/api/v1/put', methods=['POST'])
        def put():
            """写入数据"""
            data = request.json
            key = data.get('key', '').encode()
            value = data.get('value', '').encode()
            success, root_hash = self.db.put(key, value)
            return jsonify({
                'success': success,
                'merkle_root': root_hash.hex() if root_hash else None
            })
        
        @self.app.route('/api/v1/get/<key>', methods=['GET'])
        def get(key: str):
            """读取数据"""
            version = request.args.get('version', type=int)
            value = self.db.get(key.encode(), version)
            if value:
                return jsonify({
                    'key': key,
                    'value': value.decode('utf-8', errors='ignore'),
                    'version': self.db.version_manager.get_current_version(key.encode())
                })
            return jsonify({'error': 'Key not found'}), 404
        
        @self.app.route('/api/v1/history/<key>', methods=['GET'])
        def history(key: str):
            """获取历史版本"""
            start_version = request.args.get('start_version', type=int)
            end_version = request.args.get('end_version', type=int)
            history = self.db.get_history(
                key.encode(), start_version, end_version
            )
            return jsonify({'history': history})
        
        @self.app.route('/api/v1/verify', methods=['POST'])
        def verify():
            """验证数据"""
            data = request.json
            key = data.get('key', '').encode()
            value = data.get('value', '').encode()
            proof = [bytes.fromhex(p) for p in data.get('proof', [])]
            is_valid = self.db.verify(key, value, proof)
            return jsonify({'valid': is_valid})
        
        @self.app.route('/api/v1/root', methods=['GET'])
        def root():
            """获取Merkle根哈希"""
            root_hash = self.db.get_root_hash()
            return jsonify({'merkle_root': root_hash.hex()})
        
        @self.app.route('/api/v1/batch', methods=['POST'])
        def batch():
            """批量写入"""
            data = request.json
            items = [
                (item['key'].encode(), item['value'].encode())
                for item in data.get('items', [])
            ]
            success, root_hash = self.db.batch_put(items)
            return jsonify({
                'success': success,
                'merkle_root': root_hash.hex() if root_hash else None
            })
        
        @self.app.route('/api/v1/stats', methods=['GET'])
        def stats():
            """获取统计信息"""
            return jsonify(self.db.get_stats())
        
        @self.app.route('/api/v1/transaction/begin', methods=['POST'])
        def begin_tx():
            """开始事务"""
            tx = self.db.begin_transaction()
            return jsonify({'tx_id': tx.tx_id})
        
        @self.app.route('/api/v1/transaction/<int:tx_id>/commit', methods=['POST'])
        def commit_tx(tx_id: int):
            """提交事务"""
            # 从事务管理器获取事务
            tx = None
            for t in self.db.transaction_manager.transactions.values():
                if t.tx_id == tx_id:
                    tx = t
                    break
            
            if not tx:
                return jsonify({'success': False, 'error': 'Transaction not found'}), 404
            
            success = self.db.commit_transaction(tx)
            return jsonify({'success': success})
        
        @self.app.route('/api/v1/transaction/<int:tx_id>/abort', methods=['POST'])
        def abort_tx(tx_id: int):
            """中止事务"""
            tx = None
            for t in self.db.transaction_manager.transactions.values():
                if t.tx_id == tx_id:
                    tx = t
                    break
            
            if not tx:
                return jsonify({'success': False, 'error': 'Transaction not found'}), 404
            
            self.db.abort_transaction(tx)
            return jsonify({'success': True})
    
    def run(self, debug: bool = False):
        """运行服务器"""
        self.app.run(host=self.host, port=self.port, debug=debug)

