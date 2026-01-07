import os, json
from openai import OpenAI
from state_extractor import extract_state_for_chapter, extract_tkg_for_chapter, extract_char_graph_for_chapter
from tkg_models import RelationsSnapshot, CharacterAttributes

def build_states(file_path: str, out_dir: str, api_key: str = None):
    """
    构建章节状态快照
    
    Args:
        file_path: 输入文件路径
        out_dir: 输出目录
        api_key: OpenAI API密钥
    """
    os.makedirs(out_dir, exist_ok=True)
    client = OpenAI(api_key=api_key) if (api_key or os.getenv("OPENAI_API_KEY")) else None
    
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()
    
    # 将整个文件作为一个章节处理
    chapters = [(1, "完整章节", text)]
    all_roles = set()
    rel_types = set()
    outputs = []
    
    # 确保TKG和graphs目录存在
    tkg_dir = "tkg/canon"
    graphs_dir = "graphs/canon"
    os.makedirs(tkg_dir, exist_ok=True)
    os.makedirs(graphs_dir, exist_ok=True)
    
    print(f"开始处理 1 个章节...")
    
    for cid, title, body in chapters:
        print(f"处理第 {cid} 章: {title}")
        
        # 1. 提取章节状态
        state = extract_state_for_chapter(cid, title, body, client)
        
        # 累计统计
        for r in state.relations:
            all_roles.add(r.a); all_roles.add(r.b); rel_types.add(r.type)
        for who in state.goals.keys():
            all_roles.add(who)
        
        # 保存章节状态
        out_path = os.path.join(out_dir, f"chapter_{cid:03d}.json")
        with open(out_path, "w", encoding="utf-8") as wf:
            wf.write(state.model_dump_json(indent=2))
        
        outputs.append({"chapter_id":cid, "title":title, "file":out_path})
        print(f"✅ 第 {cid} 章状态已保存到 {out_path}")
        
        # 2. 提取并保存TKG
        print(f"🔍 正在抽取第 {cid} 章TKG...")
        triples = extract_tkg_for_chapter(cid, title, body, client)
        
        tkg_path = os.path.join(tkg_dir, f"chapter_{cid:03d}.tkg.jsonl")
        with open(tkg_path, 'w', encoding='utf-8') as f:
            for triple in triples:
                f.write(triple.model_dump_json() + '\n')
        
        print(f"✅ TKG已保存到 {tkg_path} ({len(triples)} 条记录)")
        
        # 3. 提取并保存人物图
        print(f"👥 正在抽取第 {cid} 章人物图...")
        
        # 加载上一章快照（第一章没有上一章）
        prev_characters = {}
        prev_relations = RelationsSnapshot(chapter_id=cid-1, nodes=[], edges=[])
        
        char_snapshot, rel_snapshot = extract_char_graph_for_chapter(
            cid, title, body, prev_characters, prev_relations, client
        )
        
        # 保存角色属性表
        char_path = os.path.join(graphs_dir, f"chapter_{cid:03d}.characters.json")
        with open(char_path, 'w', encoding='utf-8') as f:
            f.write(char_snapshot.model_dump_json(indent=2))
        
        # 保存关系图
        rel_path = os.path.join(graphs_dir, f"chapter_{cid:03d}.relations.json")
        with open(rel_path, 'w', encoding='utf-8') as f:
            f.write(rel_snapshot.model_dump_json(indent=2))
        
        print(f"✅ 人物图已保存:")
        print(f"  - 角色属性: {char_path}")
        print(f"  - 关系图: {rel_path}")
        print(f"📊 统计: {len(char_snapshot.characters)} 个角色, {len(rel_snapshot.edges)} 条关系")
    
    # 生成索引文件
    index_path = os.path.join(out_dir, "index.json")
    with open(index_path, "w", encoding="utf-8") as wf:
        meta = {
            "worldline_id":"canon",
            "num_chapters": len(chapters),
            "roles": sorted(list(all_roles)),
            "relation_types": sorted(list(rel_types)),
            "chapters": outputs
        }
        json.dump(meta, wf, ensure_ascii=False, indent=2)
    
    print(f"✅ 索引文件已保存到 {index_path}")
    print(f"📊 统计信息:")
    print(f"  - 总章节数: {len(chapters)}")
    print(f"  - 角色数: {len(all_roles)}")
    print(f"  - 关系类型数: {len(rel_types)}")

if __name__ == "__main__":
    # 检查API密钥
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  警告：未设置OPENAI_API_KEY环境变量，将生成空状态")
    
    build_states("Chapter1-3.txt", "world_graph/canon", api_key)
