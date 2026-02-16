import json
import requests
import os
import logging

logger = logging.getLogger("TTPAnalyzer.MitreLoader")


class MitreLoader:
    URL = "https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json"
    FILE_PATH = "data/enterprise-attack.json"

    @classmethod
    def download(cls):
        """공식 MITRE ATT&CK STIX 데이터를 GitHub에서 다운로드"""
        if not os.path.exists("data"):
            os.makedirs("data")

        if not os.path.exists(cls.FILE_PATH):
            logger.info("Downloading MITRE ATT&CK data...")
            response = requests.get(cls.URL)
            with open(cls.FILE_PATH, "w", encoding="utf-8") as f:
                json.dump(response.json(), f)

    @classmethod
    def load_and_refine(cls):
        """STIX 데이터를 파싱하고 서브 기법의 맥락을 강화하여 정제"""
        with open(cls.FILE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        parent_map = {}
        objects = data.get('objects', [])

        for obj in objects:
            if obj.get('type') == 'attack-pattern':
                ext_id = next((r['external_id'] for r in obj.get('external_references', [])
                              if r['source_name'] == 'mitre-attack'), None)
                if ext_id and not obj.get('x_mitre_is_subtechnique', False):
                    parent_map[ext_id] = obj.get('name')

        refined = []
        for obj in objects:
            if obj.get('type') == 'attack-pattern' and not obj.get('revoked', False):
                ext_id = next((r['external_id'] for r in obj.get('external_references', [])
                              if r['source_name'] == 'mitre-attack'), "N/A")

                name = obj.get('name')
                description = obj.get('description', "")
                is_sub = obj.get('x_mitre_is_subtechnique', False)

                # 부모 기법의 이름을 맥락에 주입
                # - 검색 쿼리에 'SQL Injection'이 포함될 경우, 관련 서브 기법이 검색될 확률을 높임
                refined_content = f"Technique Name: {name}\n"

                if is_sub and "." in ext_id:
                    parent_id = ext_id.split(".")[0]
                    parent_name = parent_map.get(parent_id, "Unknown Parent")
                    refined_content = f"[Sub-technique of {parent_name}] " + refined_content

                refined_content += f"ID: {ext_id}\n"
                refined_content += f"Tactics: {', '.join([p['phase_name'] for p in obj.get('kill_chain_phases', [])])}\n"
                refined_content += f"Description: {description[:500]}..."

                refined.append({
                    "id": ext_id,
                    "name": name,
                    "content": refined_content,
                    "detection": obj.get('x_mitre_detection', "N/A"),
                    "tactics": [p['phase_name'] for p in obj.get('kill_chain_phases', [])],
                    "is_sub": is_sub
                })

        logger.info(f"Refined {len(refined)} MITRE techniques with sub-technique context.")
        return refined
