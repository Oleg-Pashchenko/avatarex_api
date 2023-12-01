

def save_log(*,
             avatarex_id: int = None,
             pipeline_id: int = None,
             stage_id: int = None,
             mode: str = None,
             answer: str = "",
             error: Exception = None):
    print(answer, avatarex_id, pipeline_id, stage_id, mode, error.__str__())
