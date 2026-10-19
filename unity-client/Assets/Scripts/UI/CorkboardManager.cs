using UnityEngine;
using UnityEngine.UI;
using System.Collections.Generic;

public class CorkboardManager : MonoBehaviour
{
    [SerializeField] private Transform itemContainer;
    [SerializeField] private GameObject cardPrefab;
    [SerializeField] private LineRenderer redStringPrefab;

    private List<LineRenderer> activeStrings = new List<LineRenderer>();
    private GameObject selectedCard = null;

    public void AddCard(string id, string name, bool isSuspect)
    {
        GameObject card = Instantiate(cardPrefab, itemContainer);
        card.name = id;
        card.GetComponentInChildren<Text>().text = name;
        
        // Add simple drag logic here (omitted for brevity, implement via IDragHandler)
    }

    public void ConnectCards(GameObject from, GameObject to)
    {
        LineRenderer line = Instantiate(redStringPrefab);
        line.SetPosition(0, from.transform.position);
        line.SetPosition(1, to.transform.position);
        activeStrings.Add(line);
    }

    public void ClearBoard()
    {
        foreach (var s in activeStrings) Destroy(s.gameObject);
        activeStrings.Clear();
        foreach (Transform child in itemContainer) Destroy(child.gameObject);
    }
}
