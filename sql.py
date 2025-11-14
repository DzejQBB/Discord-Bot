SQL_PER_TRACK = """
SELECT
  c.Name       AS TrackName,
  p.NickName   AS PlayerName,
  r.Score,
  ranked.Place,
  (cnt.n_chal - ranked.Place + 1) AS Points
FROM (
  SELECT
    t.ChallengeId,
    t.PlayerId,
    t.Score,
    /* rank within each challenge by Score ASC, tie-break by Id ASC */
    @rn := IF(@cur = t.ChallengeId, @rn + 1, 1) AS Place,
    @cur := t.ChallengeId AS _cur
  FROM (
    SELECT r.ChallengeId, r.PlayerId, r.Score, r.Id
    FROM records r
    ORDER BY r.ChallengeId, r.Score ASC, r.Id ASC
  ) AS t
  CROSS JOIN (SELECT @rn := 0, @cur := NULL) vars
) AS ranked
JOIN (
  SELECT ChallengeId, COUNT(*) AS n_chal
  FROM records
  GROUP BY ChallengeId
) AS cnt ON cnt.ChallengeId = ranked.ChallengeId
JOIN records r      ON r.ChallengeId = ranked.ChallengeId AND r.PlayerId = ranked.PlayerId AND r.Score = ranked.Score
JOIN players p      ON p.Id = ranked.PlayerId
JOIN challenges c   ON c.Id = ranked.ChallengeId
ORDER BY TrackName ASC, r.Score ASC, ranked.Place ASC;
"""



SQL_OVERALL = """
SELECT
  p.NickName AS PlayerName,
  s.PlayerId,
  SUM(cnt.n_chal - s.Place + 1) AS TotalPoints
FROM (
  SELECT
    t.ChallengeId,
    t.PlayerId,
    /* row number per challenge */
    @rn := IF(@cur = t.ChallengeId, @rn + 1, 1) AS Place,
    @cur := t.ChallengeId AS _cur
  FROM (
    SELECT r.ChallengeId, r.PlayerId, r.Score, r.Id
    FROM records r
    ORDER BY r.ChallengeId, r.Score ASC, r.Id ASC
  ) AS t
  CROSS JOIN (SELECT @rn := 0, @cur := NULL) vars
) AS s
JOIN (
  SELECT ChallengeId, COUNT(*) AS n_chal
  FROM records
  GROUP BY ChallengeId
) AS cnt ON cnt.ChallengeId = s.ChallengeId
JOIN players p ON p.Id = s.PlayerId
GROUP BY s.PlayerId, p.NickName
ORDER BY TotalPoints DESC, PlayerName ASC;
"""


SQL_KARMA = """
SELECT 
	challenges.Name,
    t.Score
FROM (
	SELECT 
        ChallengeId,
        SUM(Score) as Score
    FROM `rs_karma`
    GROUP BY ChallengeId
    ORDER BY Score DESC, ChallengeId ASC) as t
LEFT JOIN challenges ON challenges.Id = t.ChallengeId
"""