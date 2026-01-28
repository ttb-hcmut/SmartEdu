import json


def serialize_data(data: dict) -> dict:
        """
        Neo4j không nhận Map lồng nhau. 
        Chuyển các dict/list lồng nhau thành chuỗi JSON.
        """
        clean_data = {}
        for k, v in data.items():
            if isinstance(v, (dict, list)):
                clean_data[k] = json.dumps(v, ensure_ascii=False)
            else:
                clean_data[k] = v
        return clean_data

## Micro learning