from xml.etree import ElementTree as ET

####################################
### Generate Chargenmorphcfg.xml ###
####################################
class DAOChargen:

    _race_gender_tags = {
        "hm": "human_male",
        "hf": "human_female",
        "dm": "dwarf_male",
        "df": "dwarf_female",
        "em": "elf_male",
        "ef": "elf_female",
    }

    _vanilla_heads = (
        "_cps_p01.mop", "_cps_p02.mop", "_cps_p03.mop",
        "_cps_p04.mop", "_cps_p05.mop", "_cps_p06.mop",
        "_cps_p07.mop", "_cps_p08.mop", "_pcc_b01.mop",
    )

    _vanilla_hairs_male = (
        ("_har_blda_0", "0234"), ("_har_ha1a_0", "1"), ("_har_ha2a_0", "1"), ("_har_ha3a_0", "1"),
        ("_har_hb1a_0", "1"), ("_har_hb2a_0", "1"), ("_har_hb3a_0", "1"), ("_har_hb4a_0", "1"),
        ("_har_hc1a_0", "1"), ("_har_hc2a_0", "1"), ("_har_hc3a_0", "1"), ("_har_hc4a_0", "1"),
        ("_har_hd1a_0", "1"), ("_har_hd2a_0", "1"), ("_har_hd3a_0", "1"), ("_har_hd4a_0", "0"),
    )

    _vanilla_hairs_female = (
        ("_har_blda_0", "02"), ("_har_ha1a_0", "1"), ("_har_ha2a_0", "1"), ("_har_ha3a_0", "1"),
        ("_har_ha4a_0", "1"), ("_har_hb1a_0", "1"), ("_har_hb2a_0", "1"), ("_har_hb3a_0", "1"),
        ("_har_hb4a_0", "1"), ("_har_hc1a_0", "1"), ("_har_hc2a_0", "1"), ("_har_hc3a_0", "1"),
        ("_har_hc4a_0", "1"), ("_har_hd1a_0", "1"), ("_har_hd2a_0", "1"), ("_har_hd3a_0", "1"),
        ("_har_hd4a_0", "1"),
    )

    _vanilla_beards = (
        "", "_brd_b1a_0", "_brd_b2a_0", "_brd_b3a_0",
        "_brd_b4a_0", "_brd_b5a_0", "_brd_b6a_0",
    )

    _vanilla_hair_colors = (
        "t3_har_wht", "t3_har_bln", "t3_har_dbl",
        "t3_har_org", "t3_har_red", "t3_har_lbr",
        "t3_har_rbr", "t3_har_dbr", "t3_har_blk",
    )

    _vanilla_skin_colors = (
        "t1_skn_001", "t1_skn_002", "t1_skn_003",
        "t1_skn_004", "t1_skn_006", "t1_skn_005",
        "t1_skn_007",
    )

    _vanilla_eyes_colors = (
        "t3_eye_ice", "t3_eye_lbl", "t3_eye_dbl",
        "t3_eye_tea", "t3_eye_grn", "t3_eye_hzl",
        "t3_eye_lbr", "t3_eye_amb", "t3_eye_dbr",
        "t3_eye_gry", "t3_eye_blk",
    )

    _vanilla_eyes_makeup_colors = (
        "", "t1_mue_bl1", "t1_mue_bl2", "t1_mue_bl3", "t1_mue_gn1", "t1_mue_gn2",
        "t1_mue_gn3", "t1_mue_gr1", "t1_mue_gr2", "t1_mue_gr3", "t1_mue_or1",
        "t1_mue_or2", "t1_mue_or3", "t1_mue_pi1", "t1_mue_pi2", "t1_mue_pi3",
        "t1_mue_pu1", "t1_mue_pu2", "t1_mue_pu3", "t1_mue_re1", "t1_mue_re2",
        "t1_mue_re3", "t1_mue_ro1", "t1_mue_ro2", "t1_mue_ro3", "t1_mue_te1",
        "t1_mue_te2", "t1_mue_te3", "t1_mue_ye1", "t1_mue_ye2", "t1_mue_ye3",
    )

    _vanilla_blush_makeup_colors = (
        "", "t1_mub_br1", "t1_mub_br2", "t1_mub_br3", "t1_mub_or1",
        "t1_mub_or2", "t1_mub_or3", "t1_mub_pi1", "t1_mub_pi2", "t1_mub_pi3",
        "t1_mub_pu1", "t1_mub_pu2", "t1_mub_pu3", "t1_mub_re1", "t1_mub_re2",
        "t1_mub_re3", "t1_mub_ro1", "t1_mub_ro2", "t1_mub_ro3", "t1_mub_ta1",
        "t1_mub_ta2", "t1_mub_ta3", "t1_mub_te1", "t1_mub_te2", "t1_mub_te3",
    )

    _vanilla_lip_makeup_colors = (
        "", "t1_mul_bk1", "t1_mul_bk2", "t1_mul_bk3", "t1_mul_br1",
        "t1_mul_br2", "t1_mul_br3", "t1_mul_pi1", "t1_mul_pi2", "t1_mul_pi3",
        "t1_mul_pu1", "t1_mul_pu2", "t1_mul_pu3", "t1_mul_re1", "t1_mul_re2",
        "t1_mul_re3", "t1_mul_ro1", "t1_mul_ro2", "t1_mul_ro3", "t1_mul_ta1",
        "t1_mul_ta2", "t1_mul_ta3", "t1_mul_te1", "t1_mul_te2", "t1_mul_te3",
    )

    _vanilla_brow_stubble_colors = (
        "t1_stb_wht", "t1_stb_bln", "t1_stb_dbl",
        "t1_stb_org", "t1_stb_red", "t1_stb_lbr",
        "t1_stb_rbr", "t1_stb_dbr", "t1_stb_blk",
    )
	
    _vanilla_crew_cut_colors = (
        "t1_stb_wht", "t1_stb_bln", "t1_stb_dbl",
        "t1_stb_org", "t1_stb_red", "t1_stb_lbr",
        "t1_stb_rbr", "t1_stb_dbr", "t1_stb_blk",
    )
	
    _vanilla_tattoo_colors = (
        "T1_TAT_BLK", "T1_TAT_GRY", "T1_TAT_BRN", "T1_TAT_DBR",
        "T1_TAT_GRN", "T1_TAT_DGN", "T1_TAT_BLU", "T1_TAT_DBL",
        "T1_TAT_PUR", "T1_TAT_DPU", "T1_TAT_RED", "T1_TAT_DRD",
        "T1_TAT_ORG", "T1_TAT_YEL", "T1_TAT_PNK",
    )

    _vanilla_tattoos = (
        "uh_tat_av1_0t", "uh_tat_av2_0t", "uh_tat_av3_0t",
        "uh_tat_da1_0t", "uh_tat_da2_0t", "uh_tat_da3_0t",
        "uh_tat_dw1_0t", "uh_tat_dw2_0t", "uh_tat_p01_0t",
    )

    _vanilla_skins = (
        "uh_hed_fema_0d", "uh_hed_elfa_0d",
        "uh_hed_kida_0d", "uh_hed_masa_0d",
        "uh_hed_dwfa_0d", "uh_hed_quna_0d",
    )

    _vanilla_lists = {
        'heads'               : _vanilla_heads,
        'hairs'               : _vanilla_hairs_female,
        'beards'              : _vanilla_beards,
        'hair_colors'         : _vanilla_hair_colors,
        'skin_colors'         : _vanilla_skin_colors,
        'eyes_colors'         : _vanilla_eyes_colors,
        'eyes_makeup_colors'  : _vanilla_eyes_makeup_colors,
        'blush_makeup_colors' : _vanilla_blush_makeup_colors,
        'lip_makeup_colors'   : _vanilla_lip_makeup_colors,
        'brow_stubble_colors' : _vanilla_brow_stubble_colors,
        'crew_cut_colors'     : _vanilla_crew_cut_colors,
        'tattoo_colors'       : _vanilla_tattoo_colors,
        'tattoos'             : _vanilla_tattoos,
        'skins'               : _vanilla_skins,
    }

    @staticmethod
    def build_vanilla_chargen() -> ET.Element:
        morph_config = ET.Element("morph_config")

        morph_config.append(DAOChargen.get_vanilla_heads())
        morph_config.append(DAOChargen.get_vanilla_hairs())
        morph_config.append(DAOChargen.get_vanilla_beards())

        for element, item_list in DAOChargen._vanilla_lists.items():
            if element in ["heads", "hairs", "beards"]:
                continue
            attrib_list: list[dict[str, str]] = []
            for item in item_list:
                if isinstance(item, str): attrib_list.append({"name" : item})
            resource_block = DAOChargen.build_resource_block(element, attrib_list)
            morph_config.append(resource_block)
        return morph_config

    @staticmethod
    def get_vanilla_heads() -> ET.Element:
        """Builds the vanilla heads block"""
        heads = ET.Element("heads")
        for prefix, element in DAOChargen._race_gender_tags.items():
            attrib_list: list[dict[str, str]] = []
            for item in DAOChargen._vanilla_heads:   
                attrib_list.append({"name" : f"{prefix}{item}"})
            resource_block = DAOChargen.build_resource_block(element, attrib_list)
            heads.append(resource_block)
        return heads
    
    @staticmethod
    def get_vanilla_hairs() -> ET.Element:
        """Builds the vanilla hairs block"""
        hairs = ET.Element("hairs")
        for prefix, element in DAOChargen._race_gender_tags.items():
            if prefix.endswith("f"): 
                item_list = DAOChargen._vanilla_hairs_female 
            else: item_list = DAOChargen._vanilla_hairs_male
            attrib_list: list[dict[str, str]] = []
            for item in item_list:   
                attrib_list.append({
                    "name" : f"{prefix}{item[0]}",
                    "cut" : f"{item[1]}"
                    })   
            resource_block = DAOChargen.build_resource_block(element, attrib_list)
            hairs.append(resource_block)
        return hairs

    @staticmethod
    def get_vanilla_beards() -> ET.Element:
        """Builds the vanilla beards block"""
        beards = ET.Element("beards")
        for prefix, element in DAOChargen._race_gender_tags.items():
            if prefix.endswith("f") or prefix.startswith("e"):
                continue
            attrib_list: list[dict[str, str]] = []
            for item in DAOChargen._vanilla_beards:  
                attrib_list.append({"name" : f"{prefix.upper()}{item}"})
            resource_block = DAOChargen.build_resource_block(element, attrib_list)
            beards.append(resource_block)
        return beards

    @staticmethod
    def build_resource_block(tag: str, attrib_list: list[dict[str, str]]) -> ET.Element:
        """Builds a block of xml resource elements"""
        resource_block = ET.Element(tag)
        for attrib in attrib_list:
            resource = DAOChargen.build_resource(attrib)
            resource_block.append(resource)
        return resource_block

    @staticmethod
    def build_resource(attrib: dict[str, str]) -> ET.Element:
        """Builds an xml resource element"""
        resource = ET.Element("resource", attrib)
        return resource
        
    @staticmethod
    def get_resource_type(base_name: str, ext: str) -> str:
        """Check which type of chargen resource the file is."""
        match_map = {
            "mop": [("heads", "_")],
            "mmh": [("hairs", "_har_"), ("beards", "_brd_")],
            "tnt": [
                ("hair_colors", "_har_"),
                ("skin_colors", "_skn_"),
                ("eyes_colors", "_eye_"),
                ("eyes_makeup_colors", "_mue_"),
                ("blush_makeup_colors", "_mub_"),
                ("lip_makeup_colors", "_mul_"),
                ("brow_stubble_colors", "_stb_"),
                ("crew_cut_colors", "_stb_"),
                ("tattoo_colors", "_tat_"),
            ],
            "dds": [("tattoos", "uh_tat_"), ("skins", "uh_hed_")],
        }
        resource_type: str = ""
        for type_name, substr in match_map.get(ext, ()):
            if not substr in base_name:
                continue
            resource_type = type_name
            break
        # Filter out if it's already a vanilla file
        vanilla_list = DAOChargen._vanilla_lists.get(resource_type, ())
        if vanilla_list and isinstance(vanilla_list[0], tuple):
            endings = tuple(item[0] for item in vanilla_list)
        else: endings = tuple(vanilla_list)
        if base_name.endswith(endings):
            resource_type = ""
        return resource_type

    @staticmethod
    def add_resource(chargenmorph: ET.Element, file_name: str, resource_type: str) -> None:
        """Create resource element and add to resource block"""
        if not resource_type == "heads":
           file_name = file_name.rsplit(".", 1)[0]

        if resource_type == "hairs":
            attrib = {"name" : file_name, "cut" : "1"}
        else:
            attrib = {"name" : file_name}
        resource = DAOChargen.build_resource(attrib)

        race = DAOChargen._race_gender_tags.get(file_name[:2])
        if race:
            parent = chargenmorph.find(f"{resource_type}/{race}")
        else:
            parent = chargenmorph.find(resource_type)
        if isinstance(parent, ET.Element): 
            parent.append(resource)