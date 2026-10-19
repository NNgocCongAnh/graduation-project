using System;
using System.Collections.Generic;

[Serializable]
public class CaseData
{
    public string caseId;
    public string title;
    public string description;
    public List<Suspect> suspects;
    public List<Evidence> evidence;
    public string groundTruth;
}

[Serializable]
public class Suspect
{
    public string id;
    public string name;
    public string description;
    public string alibi;
}

[Serializable]
public class Evidence
{
    public string id;
    public string name;
    public string description;
    public string type; // e.g., "forensic", "testimony"
}
