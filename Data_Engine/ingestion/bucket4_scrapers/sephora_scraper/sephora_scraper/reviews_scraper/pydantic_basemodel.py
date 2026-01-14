from pydantic import BaseModel, validator, root_validator, Field
from typing import Optional, List


class TypeValue(BaseModel):
    Value: Optional[str] = None


class ContextDataValues(BaseModel):
    skin_tone: Optional[TypeValue] = Field(alias='skinTone', default=None)
    eye_color: Optional[TypeValue] = Field(alias='eyeColor', default=None)
    skin_type: Optional[TypeValue] = Field(alias='skinType', default=None)
    hair_color: Optional[TypeValue] = Field(alias='hairColor', default=None)
    is_staff: Optional[TypeValue] = Field(alias='StaffContext', default=None)
    incentivized_review: Optional[TypeValue] = Field(alias='IncentivizedReview', default=None)

    @validator('is_staff', 'incentivized_review')
    def str_to_int(cls, field):
        """Transforms 'true'/'false' -> 1/0."""
        if field.Value.lower() == 'true':
            field.Value = 1
            return field.Value
        elif field.Value.lower() == 'false':
            field.Value = 0
            return field.Value

    @validator('skin_tone', 'eye_color', 'skin_type', 'hair_color')
    def get_value(cls, field):
        return field.Value


class Result(BaseModel):
    author_id: Optional[int] = Field(alias='AuthorId', default=None)
    rating: Optional[int] = Field(alias='Rating', default=None)
    is_recommended: Optional[int] = Field(alias='IsRecommended', default=None)
    helpfulness: Optional[float] = Field(alias='Helpfulness', default=None)
    total_feedback_count: Optional[int] = Field(alias='TotalFeedbackCount', default=None)
    total_neg_feedback_count: Optional[int] = Field(alias='TotalNegativeFeedbackCount', default=None)
    total_pos_feedback_count: Optional[int] = Field(alias='TotalPositiveFeedbackCount', default=None)
    submission_time: Optional[str] = Field(alias='SubmissionTime', default=None)
    review_text: Optional[str] = Field(alias='ReviewText', default=None)
    review_title: Optional[str] = Field(alias='Title', default=None)
    context_values: ContextDataValues = Field(alias='ContextDataValues', exclude=True)  # auxiliary field

    @validator('review_text', 'review_title')
    def clear_text(cls, field):
        """Clears the review text and title from extraneous characters."""
        if field is not None:
            field = field.replace("'", '’').replace("\n", '').replace('"', '“').replace(' ', '').replace(' ', '')
        return field

    @validator('submission_time')
    def truncate_time(cls, field):
        """Transforms '2022-06-23T14:04:17.000+00:00' -> '2022-06-23'."""
        return field[:10]

    @root_validator  # for context_values
    def get_nested_values(cls, values):
        """Extracts all dictionaries from context_values"""
        for k, v in values['context_values'].dict().items():
            if v is not None:
                if type(v) == str:
                    values[f'{k}'] = f'{v}'
                else:
                    values[f'{k}'] = int(v)
            else:
                values[f'{k}'] = None
        return values


class ReviewInfo(BaseModel):
    Results: List[Result]