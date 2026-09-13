SELECT 

    adversary_id,
    adversary,

    filter(transform(split(coalesce(rasd_ids, ''), '[|]'), x -> upper(trim(x))), x -> x <> '') AS members_rasd_reports,
    filter(transform(split(coalesce(targeted_country, ''), '[|]'), x -> upper(trim(x))), x -> x <> '') AS country_members,
    
    -- Generate group_key by hashing sorted country values
    CASE 
      WHEN coalesce(targeted_country, '') = '' 
      THEN lower(md5('Unknown'))
      ELSE lower(md5(array_join(
          array_sort(
            filter(transform(split(targeted_country, '[|]'), x -> upper(trim(x))), x -> x <> '')
          ),
          '|'
        )))
    END AS country_group_key

FROM {{ source_schema }}.adversary