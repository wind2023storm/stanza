# This is the XPOS factory method generated automatically from models.pos.build_xpos_vocab_factory.
# Please don't edit it!

from stanza.models.pos.vocab import WordVocab, XPOSVocab

def xpos_vocab_factory(data, shorthand):
    if shorthand in ["af_afribooms", "ar_padt", "bg_btb", "cs_cac", "cs_cltt", "cs_fictree", "cs_pdt", "en_partut", "fr_partut", "gd_arcosg", "gl_ctg", "gl_treegal", "grc_perseus", "hr_set", "is_icepahc", "it_isdt", "it_partut", "it_postwita", "it_twittiro", "it_vit", "it_combined", "la_perseus", "lt_alksnis", "lv_lvtb", "ro_nonstandard", "ro_rrt", "ro_simonero", "sk_snk", "sl_ssj", "sl_sst", "sr_set", "ta_ttb", "uk_iu"]:
        return XPOSVocab(data, shorthand, idx=2, sep="")
    elif shorthand in ["be_hse", "ca_ancora", "cop_scriptorium", "cu_proiel", "cy_ccg", "da_ddt", "de_gsd", "de_hdt", "el_gdt", "en_ewt", "en_gum", "en_combined", "es_ancora", "es_gsd", "et_edt", "et_ewt", "eu_bdt", "fa_perdt", "fa_seraji", "fi_tdt", "fr_ftb", "fr_gsd", "fro_srcmf", "fr_sequoia", "fr_spoken", "ga_idt", "got_proiel", "grc_proiel", "he_htb", "hi_hdtb", "hu_szeged", "hy_armtdp", "id_csui", "ja_gsd", "la_proiel", "lt_hse", "lzh_kyoto", "mr_ufal", "mt_mudt", "nb_bokmaal", "nn_nynorsk", "nn_nynorsklia", "orv_rnc", "orv_torot", "pcm_nsc", "pt_bosque", "pt_gsd", "qtd_sagt", "ru_gsd", "ru_syntagrus", "ru_taiga", "sa_vedic", "sme_giella", "swl_sslc", "te_mtg", "tr_boun", "tr_imst", "ug_udt", "vi_vtb", "wo_wtb", "zh_gsdsimp", "zh-hans_gsdsimp", "zh-hant_gsd", "bxr_bdt", "hsb_ufal", "ja_bccwj", "kk_ktb", "kmr_mg", "olo_kkpp"]:
        return WordVocab(data, shorthand, idx=2, ignore=["_"])
    elif shorthand in ["en_lines", "fo_farpahc", "sv_lines", "ur_udtb"]:
        return XPOSVocab(data, shorthand, idx=2, sep="-")
    elif shorthand in ["fi_ftb"]:
        return XPOSVocab(data, shorthand, idx=2, sep=",")
    elif shorthand in ["id_gsd", "ko_gsd", "ko_kaist"]:
        return XPOSVocab(data, shorthand, idx=2, sep="+")
    elif shorthand in ["la_ittb", "la_llct", "nl_alpino", "nl_lassysmall", "sv_talbanken"]:
        return XPOSVocab(data, shorthand, idx=2, sep="|")
    elif shorthand in ["pl_lfg", "pl_pdb"]:
        return XPOSVocab(data, shorthand, idx=2, sep=":")
    else:
        raise NotImplementedError('Language shorthand "{}" not found!'.format(shorthand))
