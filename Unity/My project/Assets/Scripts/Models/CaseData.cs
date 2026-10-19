using System;
using System.Collections.Generic;

[Serializable]
public class ForensicData
{
    public float ambient_temp;
    public float body_temp;
    public string livor_mortis_state;
    public string wound_description;
    public string estimated_tod_start;
    public string estimated_tod_end;
}

[Serializable]
public class VictimData
{
    public string name;
    public int age;
    public string occupation;
    public ForensicData forensic_data;
}

[Serializable]
public class SuspectData
{
    public string id;
    public string name;
    public int age;
    public string occupation;
    public string motive;
    public string alibi_start;
    public string alibi_end;
    public string alibi_statement;
    public string secret_innocent_fact;
    public bool is_culprit;
    public string image_url;
}

[Serializable]
public class EvidenceData
{
    public string id;
    public string title;
    public string location;
    public string description;
    public string linked_suspect_id;
    public bool is_crucial;
    public bool is_red_herring;
    public string image_url;
}

[Serializable]
public class GroundTruthData
{
    public string culprit_id;
    public string actual_crime_time;
    public string murder_weapon;
    public string core_contradiction;
}

[Serializable]
public class CaseDossier
{
    public string case_id;
    public string title;
    public string summary;
    public VictimData victim;
    public List<SuspectData> suspects;
    public List<EvidenceData> evidences;
    public GroundTruthData ground_truth;
}

[Serializable]
public class VerifyRequest
{
    public string case_id;
    public string selected_suspect_id;
    public List<string> selected_evidence_ids = new List<string>();
}

[Serializable]
public class VerifyResponse
{
    public string case_id;
    public bool is_correct;
    public bool culprit_identified;
    public bool crucial_evidences_identified;
    public int found_crucial_count;
    public int total_crucial_count;
    public string feedback;
    public string core_contradiction;
}
